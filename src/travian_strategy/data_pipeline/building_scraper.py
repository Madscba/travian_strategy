import csv
import logging
import os
import re
import time
from typing import Any, Optional
import pickle
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.travian_strategy.configs.directories import Directories
from src.travian_strategy.data_pipeline.building_effects import (
    categorize_effect_by_icon,
    parse_effect_value,
)
from src.travian_strategy.data_pipeline.data_models import BuildingData, BuildingEffects, BuildingLevel, ResourceCosts

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResourcesScraper:
    base_url: str = "https://knowledgebase.legends.travian.com/en-US/buildings"


    def extract_building_resource_costs_selenium(self, driver_path: str = "geckodriver", headless: bool = True) -> list[BuildingData]:
        """
        Uses Selenium with Firefox to extract comprehensive building data from the Travian buildings page.
        Requires geckodriver and selenium installed.
        Set headless=False to debug with a visible browser window.

        This method has been improved to handle:
        - Stale element references by re-fetching elements on each iteration
        - Robust navigation back to the main page with multiple retry attempts
        - Page stability waiting to ensure JavaScript rendering is complete
        - Better error recovery and logging for debugging issues
        - Proper element scrolling and interaction handling

        Args:
            driver_path: Path to geckodriver executable
            headless: Whether to run browser in headless mode

        Returns:
            List of BuildingData objects containing complete building information

        Raises:
            Exception: If browser initialization or navigation fails
        """
        url = "https://knowledgebase.legends.travian.com/en-US/buildings"
        firefox_options = FirefoxOptions()
        if headless:
            firefox_options.add_argument("--headless")
        firefox_options.add_argument("--no-sandbox")
        firefox_options.add_argument("--disable-dev-shm-usage")

        service = FirefoxService(driver_path)
        driver = None

        try:
            driver = webdriver.Firefox(service=service, options=firefox_options)
            driver.get(url)
            logger.info(f"Loaded Travian buildings page: {url}")

            # Wait for the page to load completely
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".buildingContainer"))
            )

            # Process all buildings
            all_buildings_data = self._process_all_buildings(driver)

            logger.info(f"Successfully processed {len(all_buildings_data)} buildings")

        except Exception:
            logger.exception("Fatal error in extract_building_resource_costs_selenium")
            raise
        else:
            return all_buildings_data
        finally:
            if driver:
                driver.quit()

    def _process_all_buildings(self, driver) -> list[BuildingData]:
        """
        Process all buildings on the page, handling navigation and errors robustly.

        Args:
            driver: Selenium WebDriver instance

        Returns:
            List of BuildingData objects
        """
        all_buildings_data = []

        # Get initial count of buildings
        initial_buildings = driver.find_elements(By.CSS_SELECTOR, ".buildingContainer.d-grid.gap-2.align-items-center")
        total_buildings = len(initial_buildings)
        logger.info(f"Found {total_buildings} buildings to process")

        processed_count = 0
        current_index = 0

        while processed_count < total_buildings:
            try:
                success = self._process_single_building(driver, current_index, total_buildings, processed_count, all_buildings_data)

                if success:
                    processed_count += 1

                current_index += 1

            except Exception:
                logger.exception(f"Error processing building at index {current_index}")

                # Try to recover by navigating back to main page
                if self._navigate_back_to_main_page(driver):
                    current_index += 1  # Skip this building and try the next one
                else:
                    logger.exception("Failed to recover - breaking out of loop")
                    break

        return all_buildings_data

    def _process_single_building(self, driver, current_index: int, total_buildings: int, processed_count: int, all_buildings_data: list) -> bool:
        """
        Process a single building, extracting its data and navigating back.

        Args:
            driver: Selenium WebDriver instance
            current_index: Current building index
            total_buildings: Total number of buildings
            processed_count: Number of successfully processed buildings
            all_buildings_data: List to append successful results

        Returns:
            bool: True if building was processed successfully
        """
        # Always re-fetch the current state of building elements to avoid stale references
        current_buildings = driver.find_elements(By.CSS_SELECTOR, ".buildingContainer.d-grid.gap-2.align-items-center")

        if current_index >= len(current_buildings):
            logger.warning(f"Index {current_index} out of range for {len(current_buildings)} buildings")
            return False

        if len(current_buildings) != total_buildings:
            logger.warning(f"Building count changed from {total_buildings} to {len(current_buildings)} - page may have reloaded")

        current_building = current_buildings[current_index]

        # Ensure the element is in view and interactable
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", current_building)

        # Extract building name before clicking
        building_name = current_building.find_element(By.TAG_NAME, "div").text.strip()
        logger.info(f"Processing building {processed_count + 1}/{total_buildings}: {building_name} (index {current_index})")

        # Click on the building
        driver.execute_script("arguments[0].click();", current_building)

        # Wait for building detail page to load with multiple conditions
        WebDriverWait(driver, 15).until(
            EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".buildingLevelTable")),
                EC.presence_of_element_located((By.CSS_SELECTOR, ".buildingDetailContainer"))
            )
        )

        # Wait for page stability and JavaScript rendering
        self._wait_for_page_stability(driver, timeout=10)

        # Parse the building detail page using our new function
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        building_data_list = parse_building_levels(soup, building_name)
        success = False

        if building_data_list:
            building_data = building_data_list[0]  # parse_building_levels returns a list

            # Convert to structured BuildingData model
            try:
                structured_data = self._convert_to_building_data(building_data)
                all_buildings_data.append(structured_data)
                logger.info(f"Successfully processed {building_name} with {len(structured_data.levels)} levels")
                success = True
            except Exception:
                logger.exception(f"Failed to structure data for {building_name}")
        else:
            logger.warning(f"No building data extracted for {building_name}")

        # Navigate back to the main page with robust waiting
        self._navigate_back_to_main_page(driver)

        return success

    def _navigate_back_to_main_page(self, driver) -> bool:
        """
        Robustly navigate back to the main buildings page.

        Args:
            driver: Selenium WebDriver instance

        Returns:
            bool: True if navigation was successful, False otherwise
        """
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                logger.debug(f"Navigation attempt {attempt + 1}/{max_attempts}")

                # Try to navigate back
                driver.back()

                # Wait for the main page to load with multiple fallback strategies
                try:
                    # Primary wait: buildings container
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".buildingContainer"))
                    )

                    # Secondary wait: ensure at least one building is clickable
                    WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".buildingContainer.d-grid.gap-2.align-items-center"))
                    )

                    # Additional wait for dynamic content
                    time.sleep(1)

                    # Verify we're actually on the main page by checking for multiple buildings
                    buildings = driver.find_elements(By.CSS_SELECTOR, ".buildingContainer.d-grid.gap-2.align-items-center")
                    if len(buildings) > 1:
                        logger.debug(f"Successfully navigated back to main page with {len(buildings)} buildings")
                        return True
                    else:
                        logger.warning(f"Main page loaded but only found {len(buildings)} buildings")

                except Exception as e:
                    logger.warning(f"Wait condition failed on attempt {attempt + 1}: {e}")

                # If we reach here, the wait conditions weren't met
                if attempt < max_attempts - 1:
                    logger.info("Navigation seems incomplete, retrying...")
                    time.sleep(2)  # Wait before retrying

            except Exception as e:
                logger.warning(f"Navigation attempt {attempt + 1} failed: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(2)  # Wait before retrying

                    # Try to refresh the page as a fallback
                    try:
                        driver.refresh()
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".buildingContainer"))
                        )
                        logger.info("Page refresh successful")
                    except Exception:
                        logger.warning("Page refresh also failed")
                    else:
                        return True

        logger.error("All navigation attempts failed")
        return False

    def _wait_for_page_stability(self, driver, timeout: int = 10) -> bool:
        """
        Wait for the page to be stable and fully loaded.

        Args:
            driver: Selenium WebDriver instance
            timeout: Maximum time to wait in seconds

        Returns:
            bool: True if page is stable, False if timeout
        """
        try:
            # Wait for document ready state
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            # Wait for any pending AJAX requests to complete (if jQuery is available)
            try:
                WebDriverWait(driver, 2).until(
                    lambda d: d.execute_script("return typeof jQuery !== 'undefined' ? jQuery.active == 0 : true")
                )
            except Exception:
                # jQuery might not be available, continue anyway
                logger.debug("jQuery not available or AJAX wait failed")

            # Additional wait for React to finish rendering
            time.sleep(1)

        except Exception as e:
            logger.warning(f"Page stability wait failed: {e}")
            return False
        else:
            return True

    def _extract_level_effects(self, level_data: dict[str, Any], building_id: str) -> Optional[BuildingEffects]:
        """
        Extract building effects from level data.

        Args:
            level_data: Raw level data containing effect values
            building_id: Building identifier for context

        Returns:
            BuildingEffects object or None if no effects found
        """
        effects_found = {}

        # Look for effect data in the level data
        for key, value in level_data.items():
            if key in ["storage_capacity", "production_bonus", "training_time_reduction",
                       "build_time_reduction", "population_bonus","production_type", "offensive_bonus",
                       "defensive_bonus", "merchant_capacity", "culture_points_bonus"] and value is not None:
                if key == "production_type":
                    #production type must be paired with production bonus
                    if "production_bonus" in effects_found:
                        effects_found[key] = value
                else:
                    effects_found[key] = value


        if not effects_found:
            return None

        # Map extracted effects to BuildingEffects model fields
        effect_args = {}

        # Handle storage capacity
        if "storage_capacity" in effects_found:
            effect_args["storage_capacity"] = int(effects_found["storage_capacity"])

        # Handle population bonus
        if "population_bonus" in effects_found:
            effect_args["population_bonus"] = int(effects_found["population_bonus"])

        # Handle training time reduction
        if "training_time_reduction" in effects_found:
            effect_args["training_time_reduction"] = float(effects_found["training_time_reduction"])

        # Handle build time reduction
        if "build_time_reduction" in effects_found:
            effect_args["build_time_reduction"] = float(effects_found["build_time_reduction"])

        # Handle build cost reduction
        if "build_cost_reduction" in effects_found:
            effect_args["build_cost_reduction"] = float(effects_found["build_cost_reduction"])

        # Handle military bonuses
        if "offensive_bonus" in effects_found:
            effect_args["offensive_bonus"] = float(effects_found["offensive_bonus"])

        if "defensive_bonus" in effects_found:
            effect_args["defensive_bonus"] = float(effects_found["defensive_bonus"])

        # Handle merchant capacity
        if "merchant_capacity" in effects_found:
            effect_args["merchant_capacity"] = int(effects_found["merchant_capacity"])

        # Handle culture points bonus
        if "culture_points_bonus" in effects_found:
            effect_args["culture_points_bonus"] = float(effects_found["culture_points_bonus"])

        # Handle production bonuses
        production_bonuses = {}
        if "production_type" in effects_found:
            production_bonuses[effects_found["production_type"]] = float(effects_found["production_bonus"])
            effect_args["production_bonus"] = production_bonuses

        # Handle any remaining effects in the other_effects field
        other_effects = {}
        handled_effects = {"storage_capacity", "population_bonus", "training_time_reduction",
                          "build_time_reduction", "build_cost_reduction", "offensive_bonus",
                          "defensive_bonus", "merchant_capacity", "culture_points_bonus",
                          "production_bonus"}

        for effect_type, value in effects_found.items():
            if effect_type not in handled_effects:
                other_effects[effect_type] = value

        if other_effects:
            effect_args["other_effects"] = other_effects

        try:
            return BuildingEffects(**effect_args)
        except Exception as e:
            logger.warning(f"Failed to create BuildingEffects for {building_id}: {e}")
            return None

    def _convert_to_building_data(self, raw_data: dict[str, Any]) -> BuildingData:
        """
        Convert raw parsed data to structured BuildingData model.

        Args:
            raw_data: Dictionary containing parsed building data

        Returns:
            BuildingData object with validated and structured data

        Raises:
            ValueError: If required data is missing or invalid
        """
        building_name = raw_data.get("building_name", "Unknown")
        building_id = raw_data.get("building_id", "unknown")
        levels_data = raw_data.get("levels", [])

        if not levels_data:
            msg = f"No level data found for building: {building_name}"
            raise ValueError(msg)

        # Convert level data to BuildingLevel objects
        building_levels = []
        for level_data in levels_data:
            try:
                # Extract resource costs
                resource_cost = ResourceCosts(
                    wood=level_data.get("wood", 0),
                    clay=level_data.get("clay", 0),
                    iron=level_data.get("iron", 0),
                    crop=level_data.get("crop", 0)
                )

                # Extract building effects
                effects = self._extract_level_effects(level_data, building_id)

                # Create building level object
                building_level = BuildingLevel(
                    level=level_data.get("level", 1),
                    resource_cost=resource_cost,
                    build_time=level_data.get("time", 0),
                    population=level_data.get("population", 0),
                    culture_points=level_data.get("culture_points", 0),
                    effects=effects
                )

                building_levels.append(building_level)

            except Exception as e:
                logger.warning(f"Failed to process level {level_data.get('level', 'unknown')} for {building_name}: {e}")
                continue

        if not building_levels:
            msg = f"No valid level data could be processed for building: {building_name}"
            raise ValueError(msg)

        # Determine category based on building_id or name
        category = self._determine_building_category(building_id, building_name)

        return BuildingData(
            building_name=building_name,
            building_id=building_id,
            category=category,
            max_level=max(level.level for level in building_levels),
            levels=building_levels
        )


    def _determine_building_category(self, building_id: str, building_name: str) -> str:
        """
        Determine building category based on ID or name.

        Args:
            building_id: Building identifier (e.g., 'g15')
            building_name: Building name

        Returns:
            Building category string
        """
        # Resource buildings
        resource_buildings = {
            "g1": "Resources",  # Woodcutter
            "g2": "Resources",  # Clay Pit
            "g3": "Resources",  # Iron Mine
            "g4": "Resources",  # Cropland
            "g5": "Resources",  # Sawmill
            "g6": "Resources",  # Brickyard
            "g7": "Resources",  # Iron Foundry
            "g8": "Resources",  # Grain Mill
            "g9": "Resources",  # Bakery
        }

        # Military buildings
        military_buildings = {
            "g13": "Military",  # Smithy
            "g14": "Military",  # Tournament Square
            "g16": "Military",  # Rally Point
            "g19": "Military",  # Barracks
            "g20": "Military",  # Stable
            "g21": "Military",  # Workshop
            "g22": "Military",  # Academy
            "g29": "Military",  # Great Barracks
            "g30": "Military",  # Great Stable
            "g31": "Military",  # City Wall
            "g32": "Military",  # Earth Wall
            "g33": "Military",  # Palisade
            "g37": "Military",  # Hero's Mansion
        }

        if building_id in resource_buildings:
            return resource_buildings[building_id]
        elif building_id in military_buildings:
            return military_buildings[building_id]
        else:
            # Default to Infrastructure for unknown buildings
            return "Infrastructure"

def parse_building_levels(soup: BeautifulSoup, building_name: Optional[str] = None) -> list[dict[str, Any]]:
    """
    Parse building levels from HTML content of a Travian knowledge base building detail page.

    IMPORTANT: This function requires HTML content that has been fully rendered by JavaScript.
    The Travian knowledge base uses React/JavaScript to dynamically generate the building
    level tables. Static HTML parsing will not work - you must use Selenium WebDriver
    to load the page and execute JavaScript before parsing.

    This function extracts building level data using the specified approach:
    1. Use div.buildingLevelHeader.buildingLevelRow to identify column structure
    2. Extract div elements with grid-area styles to determine data categories
    3. Parse buildingLevelRowData to extract level information
    4. Map bt-with-tooltip icon classes to data types

    Args:
        soup: BeautifulSoup object containing the JAVASCRIPT-RENDERED building detail page HTML
        building_name: Optional building name to include in the result

    Returns:
        List of dictionaries containing building level data

    Raises:
        ValueError: If required HTML elements are not found
        AttributeError: If HTML structure is unexpected
    """
    logger.info(f"Parsing building levels for: {building_name or 'Unknown building'}")

    try:
        # Step 1: Find the building level table and validate structure
        level_table, level_header = _find_building_table_elements(soup)

        # Step 2: Extract column definitions from header grid areas
        header_columns = _extract_header_columns(level_header)

        # Step 3: Extract building name if not provided
        building_name = building_name or _extract_building_name(soup)

        # Step 4: Parse level data rows
        level_data = _parse_all_level_rows(level_table, header_columns)

        if not level_data:
            logger.warning("No level data found")
            return []

        # Step 5: Structure the result
        result = {
            "building_name": building_name,
            "building_id": _extract_building_id(soup),
            "levels": level_data
        }

        logger.info(f"Successfully parsed {len(level_data)} levels for {building_name}")

    except Exception:
        logger.exception("Error parsing building levels")
        raise
    else:
        return [result]


def _find_building_table_elements(soup: BeautifulSoup) -> tuple:
    """Find and validate building table and header elements."""
    level_table = soup.find("div", class_=lambda x: x and "buildingLevelTable" in x)
    if not level_table:
        msg = "Building level table not found"
        raise ValueError(msg)

    level_header = level_table.find("div", class_="buildingLevelHeader buildingLevelRow")
    if not level_header:
        msg = "Building level header not found"
        raise ValueError(msg)

    return level_table, level_header


def _extract_header_columns(level_header) -> dict[str, str]:
    """Extract column definitions from header grid areas."""
    header_columns = {}
    for header_div in level_header.find_all("div", style=True):
        style = header_div.get("style", "")
        grid_area_match = re.search(r'grid-area:\s*([^;]+)', style)
        if grid_area_match:
            grid_area = grid_area_match.group(1).strip()

            # Find bt-with-tooltip element to determine data type
            tooltip_div = header_div.find("div", class_="bt-with-tooltip")
            if tooltip_div:
                icon_element = tooltip_div.find("i")
                if icon_element and icon_element.get("class"):
                    icon_classes = icon_element.get("class")
                    data_type = _determine_data_type_from_classes(icon_classes)
                    header_columns[grid_area] = data_type
                    logger.debug(f"Found column: {grid_area} -> {data_type}")

    if not header_columns:
        msg = "No valid header columns found"
        raise ValueError(msg)

    return header_columns


def _extract_building_name(soup: BeautifulSoup) -> str:
    """Extract building name from HTML."""
    building_title = soup.find("div", class_="buildingTitle")
    return building_title.get_text(strip=True) if building_title else "Unknown Building"


def _parse_all_level_rows(level_table, header_columns: dict[str, str]) -> list[dict[str, Any]]:
    """Parse all level data rows."""
    level_data = []
    level_rows = level_table.find_all("div", class_="buildingLevelRow buildingLevelRowData")

    for row in level_rows:
        try:
            row_data = _parse_level_row(row, header_columns)
            if row_data:
                level_data.append(row_data)
            else:
                logger.debug("Row data was None, skipping")
        except Exception as e:
            logger.warning(f"Failed to parse level row: {e}")
            continue

    return level_data


def _determine_data_type_from_classes(icon_classes: list[str]) -> str:
    """
    Determine the data type based on icon CSS classes.

    Maps Travian icon classes to standardized data type names.
    """
    class_str = " ".join(icon_classes) if isinstance(icon_classes, list) else str(icon_classes)

    # Check for effect icons first (specific bonuses, storage, etc.)
    effect_type = categorize_effect_by_icon(icon_classes)
    if effect_type:
        return effect_type

    # Resource type mapping based on analyzed JavaScript code
    if "icon-wood" in class_str and "Bonus" not in class_str:
        return "wood"
    elif "icon-clay" in class_str and "Bonus" not in class_str:
        return "clay"
    elif "icon-iron" in class_str and "Bonus" not in class_str:
        return "iron"
    elif "icon-crop" in class_str and "Bonus" not in class_str:
        return "crop"
    elif "icon-time" in class_str:
        return "time"
    elif "icon-population" in class_str:
        return "population"
    elif "icon-culturePoints" in class_str:
        return "culture_points"
    elif "allResources" in class_str or "sum" in class_str:
        return "total_resources"
    else:
        # Default to the class name for unknown types
        return class_str.replace("icon-", "").replace("travianImageMisc", "").strip()


def _parse_level_row(row, header_columns: dict[str, str]) -> Optional[dict[str, Any]]:
    """
    Parse a single building level row to extract data values.

    Args:
        row: BeautifulSoup element representing a level row
        header_columns: Mapping of grid areas to data types

    Returns:
        Dictionary containing parsed level data or None if parsing fails
    """
    row_data = {}

    # Look for cells with grid-area styles (can be direct div or inside valueWithIcon wrapper)
    cells_with_style = row.find_all("div", style=True)

    for cell in cells_with_style:
        style = cell.get("style", "")
        #get
        grid_area_match = re.search(r'grid-area:\s*([^;]+)', style)

        if grid_area_match:
            grid_area = grid_area_match.group(1).strip()
            data_type = header_columns.get(grid_area)

            try:
                # Extract text content and clean it
                cell_text = cell.get_text(strip=True)

                # Handle level column specially
                if grid_area == "lvl":
                    # Level should be an integer
                    numeric_value = re.sub(r'[^\d]', '', cell_text)
                    row_data["level"] = int(numeric_value) if numeric_value else 0
                elif data_type in ["wood", "clay", "iron", "crop", "total_resources", "population", "culture_points"]:
                    # Remove commas and other formatting
                    numeric_value = re.sub(r'[^\d]', '', cell_text)
                    row_data[data_type] = int(numeric_value) if numeric_value else 0
                elif data_type == "time":
                    # Parse time format (HH:MM:SS or seconds)
                    row_data[data_type] = _parse_time_value(cell_text)
                elif data_type in ["storage_capacity", "production_bonus", "training_time_reduction",
                                   "build_time_reduction", "population_bonus", "offensive_bonus",
                                   "defensive_bonus", "merchant_capacity", "culture_points_bonus"]:

                    # Parse effect values using specialized function
                    production_value, production_type = parse_effect_value(cell_text, data_type)
                    if production_value is not None:
                        row_data[data_type] = production_value
                    else:
                        row_data[data_type] = cell_text  # Fallback to raw tex

                    row_data['production_type'] = production_type
                elif data_type:
                    # Store as string for known types
                    row_data[data_type] = cell_text

            except (ValueError, AttributeError) as e:
                logger.warning(f"Failed to parse cell value for {data_type}: {e}")
                if data_type:
                    row_data[data_type] = cell_text  # Fallback to raw text

    # Ensure we have at least a level number
    if "level" not in row_data:
        return None

    return row_data


def _parse_time_value(time_str: str) -> int:
    """
    Parse time string and convert to seconds.

    Supports formats like:
    - "01:23:45" (HH:MM:SS)
    - "123" (seconds)
    - "1h 23m 45s"
    """
    if not time_str:
        return 0

    # Try HH:MM:SS format first
    time_match = re.match(r'(\d{1,2}):(\d{2}):(\d{2})', time_str)
    if time_match:
        hours, minutes, seconds = map(int, time_match.groups())
        return hours * 3600 + minutes * 60 + seconds

    # Try to extract just numbers (assume seconds)
    numeric_match = re.search(r'\d+', time_str)
    if numeric_match:
        return int(numeric_match.group())

    return 0


def _extract_building_id(soup: BeautifulSoup) -> str:
    """
    Extract building ID from the HTML content.

    Looks for building identifier in various locations.
    """
    # Try to find building image with class like "building_g15"
    building_imgs = soup.find_all("i")
    main_img = building_imgs[1] #The first item is the main building, the second is the level icon

    class_ = main_img.get("class", [])
    for class_name in class_:
        if class_name.startswith("building_g"):
            return class_name.replace("building_", "")

    return "unknown"


def main():
    """
    Main function demonstrating the usage of the building data extraction functionality.
    """
    logger.info("Starting Travian building data extraction")

    try:
        scraper = ResourcesScraper()

        buildings_data = scraper.extract_building_resource_costs_selenium(
            driver_path="/opt/homebrew/bin/geckodriver",
            headless=True  # Set to False for debugging
        )

        logger.info(f"Successfully extracted data for {len(buildings_data)} buildings")

        # Example: Print summary for each building
        for building in buildings_data:
            logger.info(f"Building: {building.building_name} ({building.building_id})")
            logger.info(f"  Category: {building.category}")
            logger.info(f"  Max Level: {building.max_level}")
            logger.info(f"  Levels available: {len(building.levels)}")

            # Print first level costs as example
            if building.levels:
                first_level = building.levels[0]
                logger.info(f"  Level 1 costs: {first_level.resource_cost.wood}w, {first_level.resource_cost.clay}c, "
                           f"{first_level.resource_cost.iron}i, {first_level.resource_cost.crop}cr")

        # Optionally export to CSV
        export_to_csv(buildings_data, Directories.DATA_FOLDER / "building_resource_costs.csv")
        #export buildings data as pickle
        import pickle

        logger.info("Exported building data to CSV and pickle formats")

    except Exception:
        logger.exception("Error in main execution")
        raise
    else:
        return buildings_data

def export_to_pickle(buildings_data: list[BuildingData], filename: str):
    """
    Export building data to a pickle file.
    Args:
        buildings_data: List of BuildingData objects
        filename: Output pickle filename
    """

    with open(Directories.DATA_FOLDER / "building_resource_costs.pkl", "wb") as f:
        pickle.dump(buildings_data, f)

def export_to_csv(buildings_data: list[BuildingData], filename: str):
    """
    Export building data to CSV format including comprehensive building effects.

    The CSV includes the following columns:
    - Basic building info: building_name, building_id, category, level
    - Resource costs: wood, clay, iron, crop, total_resources
    - Build requirements: build_time, population, culture_points
    - Effect indicators: has_effects (Yes/No), effect_type (categories), effect_description (human-readable)
    - Production bonuses: production_bonus_type, production_value
    - Specific effects: storage_capacity, population_bonus, training_time_reduction_pct,
                      build_time_reduction_pct, build_cost_reduction_pct, offensive_bonus_pct,
                      defensive_bonus_pct, merchant_capacity, culture_points_bonus_pct
    - Other effects: other_effects (for any additional building effects)

    Effect types include:
    - Production Bonus: Increases resource production (wood, clay, iron, crop)
    - Storage: Increases storage capacity for resources
    - Population: Adds population points
    - Training Time: Reduces unit training time
    - Build Time: Reduces construction time for buildings
    - Build Cost: Reduces construction cost
    - Military: Offensive/defensive bonuses for troops
    - Trade: Increases merchant carrying capacity
    - Culture: Increases culture point generation
    - Other: Any other special effects

    Args:
        buildings_data: List of BuildingData objects
        filename: Output CSV filename
    """
    logger.info(f"Exporting building data to {filename}")
    # If file does not exist, create it
    dirname = os.path.dirname(filename)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'building_name', 'building_id', 'category', 'level',
            'wood', 'clay', 'iron', 'crop', 'total_resources',
            'build_time', 'population', 'culture_points',
            # Building Effects columns
            'has_effects', 'effect_type', 'effect_description',
            'production_bonus_type', 'production_value',
            'storage_capacity', 'population_bonus',
            'training_time_reduction_pct', 'build_time_reduction_pct', 'build_cost_reduction_pct',
            'offensive_bonus_pct', 'defensive_bonus_pct',
            'merchant_capacity', 'culture_points_bonus_pct',
            'other_effects'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for building in buildings_data:
            for level in building.levels:
                # Get effect summary for this level
                effects_summary = _get_effects_summary_for_csv(level.effects)

                row_data = {
                    'building_name': building.building_name,
                    'building_id': building.building_id,
                    'category': building.category,
                    'level': level.level,
                    'wood': level.resource_cost.wood,
                    'clay': level.resource_cost.clay,
                    'iron': level.resource_cost.iron,
                    'crop': level.resource_cost.crop,
                    'total_resources': level.resource_cost.total,
                    'build_time': level.build_time,
                    'population': level.population,
                    'culture_points': level.culture_points,
                }

                # Add effects data
                row_data.update(effects_summary)
                writer.writerow(row_data)

    logger.info(f"Successfully exported building data to {filename}")


def _get_effects_summary_for_csv(effects: Optional['BuildingEffects']) -> dict[str, Any]:
    """
    Generate a CSV-friendly summary of building effects.

    Args:
        effects: BuildingEffects object or None

    Returns:
        Dictionary with effect data formatted for CSV export
    """
    if not effects or not effects.has_effects:
        return {
            'has_effects': 'No',
            'effect_type': '',
            'effect_description': '',
            'production_bonus_type': '',
            'production_value': '',
            'storage_capacity': '',
            'population_bonus': '',
            'training_time_reduction_pct': '',
            'build_time_reduction_pct': '',
            'build_cost_reduction_pct': '',
            'offensive_bonus_pct': '',
            'defensive_bonus_pct': '',
            'merchant_capacity': '',
            'culture_points_bonus_pct': '',
            'other_effects': ''
        }

    # Determine primary effect type and description
    effect_types = []
    effect_descriptions = []

    if effects.production_bonus:
        for resource_type, bonus_value in effects.production_bonus.items():
            effect_types.append("Production Bonus")
            effect_descriptions.append(f"{resource_type.title()} production +{bonus_value}%")

    if effects.storage_capacity is not None:
        effect_types.append("Storage")
        effect_descriptions.append(f"Storage capacity +{effects.storage_capacity}")

    if effects.population_bonus is not None:
        effect_types.append("Population")
        effect_descriptions.append(f"Population +{effects.population_bonus}")

    if effects.training_time_reduction is not None:
        effect_types.append("Training Time")
        effect_descriptions.append(f"Training time -{effects.training_time_reduction}%")

    if effects.build_time_reduction is not None:
        effect_types.append("Build Time")
        effect_descriptions.append(f"Construction time -{effects.build_time_reduction}%")

    if effects.build_cost_reduction is not None:
        effect_types.append("Build Cost")
        effect_descriptions.append(f"Construction cost -{effects.build_cost_reduction}%")

    if effects.offensive_bonus is not None:
        effect_types.append("Military")
        effect_descriptions.append(f"Offensive strength +{effects.offensive_bonus}%")

    if effects.defensive_bonus is not None:
        effect_types.append("Military")
        effect_descriptions.append(f"Defensive strength +{effects.defensive_bonus}%")

    if effects.merchant_capacity is not None:
        effect_types.append("Trade")
        effect_descriptions.append(f"Merchant capacity +{effects.merchant_capacity}")

    if effects.culture_points_bonus is not None:
        effect_types.append("Culture")
        effect_descriptions.append(f"Culture points +{effects.culture_points_bonus}%")

    if effects.other_effects:
        for effect_name, effect_value in effects.other_effects.items():
            effect_types.append("Other")
            effect_descriptions.append(f"{effect_name}: {effect_value}")

    # Format production bonus for CSV
    prod_bonus_type = ""
    prod_value = ""
    if effects.production_bonus:
        resources = list(effects.production_bonus.keys())
        values = list(effects.production_bonus.values())
        prod_bonus_type = ", ".join(resources)
        prod_value = ", ".join([f"{v}%" for v in values]) if prod_bonus_type == 'percentage' else ", ".join([str(v) for v in values])

    return {
        'has_effects': 'Yes',
        'effect_type': "; ".join(effect_types),
        'effect_description': "; ".join(effect_descriptions),
        'production_bonus_type': prod_bonus_type,
        'production_value': prod_value,
        'storage_capacity': effects.storage_capacity if effects.storage_capacity is not None else '',
        'population_bonus': effects.population_bonus if effects.population_bonus is not None else '',
        'training_time_reduction_pct': f"{effects.training_time_reduction}%" if effects.training_time_reduction is not None else '',
        'build_time_reduction_pct': f"{effects.build_time_reduction}%" if effects.build_time_reduction is not None else '',
        'build_cost_reduction_pct': f"{effects.build_cost_reduction}%" if effects.build_cost_reduction is not None else '',
        'offensive_bonus_pct': f"{effects.offensive_bonus}%" if effects.offensive_bonus is not None else '',
        'defensive_bonus_pct': f"{effects.defensive_bonus}%" if effects.defensive_bonus is not None else '',
        'merchant_capacity': effects.merchant_capacity if effects.merchant_capacity is not None else '',
        'culture_points_bonus_pct': f"{effects.culture_points_bonus}%" if effects.culture_points_bonus is not None else '',
        'other_effects': "; ".join([f"{k}: {v}" for k, v in effects.other_effects.items()]) if effects.other_effects else ''
    }


if __name__ == "__main__":
    main()
