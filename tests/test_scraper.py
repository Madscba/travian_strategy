import pytest
from bs4 import BeautifulSoup
from unittest.mock import Mock, patch
from travian_strategy.data_pipeline.scraper import (
    parse_building_levels,
    _determine_data_type_from_classes,
    _parse_level_row,
    _parse_time_value,
    _extract_building_id,
    ResourcesScraper
)
from travian_strategy.data_pipeline.models import (
    ResourceCosts,
    BuildingLevel,
    BuildingData,
    BuildingEffects
)
from travian_strategy.data_pipeline.building_effects import (
    parse_effect_value,
    get_effect_type_from_icon,
    categorize_effect_by_icon
)


class TestParseBuildingLevels:
    """Test cases for the parse_building_levels function."""

    def test_parse_building_levels_valid_html(self):
        """Test parsing valid HTML structure with JavaScript-rendered content."""
        # This HTML represents what would be available after JavaScript execution
        html_content = """
        <div class="buildingLevelTable effectCount3">
            <div class="buildingLevelHeader buildingLevelRow">
                <div style="grid-area: lvl;">Level</div>
                <div style="grid-area: r1;">
                    <div class="bt-with-tooltip">
                        <i class="travianImageMisc version-4 size-24 icon-wood"></i>
                    </div>
                </div>
                <div style="grid-area: r2;">
                    <div class="bt-with-tooltip">
                        <i class="travianImageMisc version-4 size-24 icon-clay"></i>
                    </div>
                </div>
                <div style="grid-area: r3;">
                    <div class="bt-with-tooltip">
                        <i class="travianImageMisc version-4 size-24 icon-iron"></i>
                    </div>
                </div>
                <div style="grid-area: r4;">
                    <div class="bt-with-tooltip">
                        <i class="travianImageMisc version-4 size-24 icon-crop"></i>
                    </div>
                </div>
                <div style="grid-area: time;">
                    <div class="bt-with-tooltip">
                        <i class="travianImageMisc version-4 size-24 icon-time"></i>
                    </div>
                </div>
                <div style="grid-area: pop;">
                    <div class="bt-with-tooltip">
                        <i class="travianImageMisc version-4 size-24 icon-population"></i>
                    </div>
                </div>
            </div>
            <div class="buildingLevelRow buildingLevelRowData">
                <div class="valueWithIcon" style="grid-area: lvl;">1</div>
                <div class="valueWithIcon" style="grid-area: r1;">70</div>
                <div class="valueWithIcon" style="grid-area: r2;">40</div>
                <div class="valueWithIcon" style="grid-area: r3;">60</div>
                <div class="valueWithIcon" style="grid-area: r4;">20</div>
                <div class="valueWithIcon" style="grid-area: time;">00:03:06</div>
                <div class="valueWithIcon" style="grid-area: pop;">2</div>
            </div>
            <div class="buildingLevelRow buildingLevelRowData">
                <div class="valueWithIcon" style="grid-area: lvl;">2</div>
                <div class="valueWithIcon" style="grid-area: r1;">90</div>
                <div class="valueWithIcon" style="grid-area: r2;">50</div>
                <div class="valueWithIcon" style="grid-area: r3;">75</div>
                <div class="valueWithIcon" style="grid-area: r4;">25</div>
                <div class="valueWithIcon" style="grid-area: time;">00:04:36</div>
                <div class="valueWithIcon" style="grid-area: pop;">1</div>
            </div>
        </div>
        <div class="buildingTitle">Main Building</div>
        <i class="travianBuildingImage version-4 size-32 tribe-1 building_g15"></i>
        """

        soup = BeautifulSoup(html_content, 'html.parser')
        result = parse_building_levels(soup)

        assert len(result) == 1
        building_data = result[0]
        assert building_data["building_name"] == "Main Building"
        assert building_data["building_id"] == "g15"
        assert len(building_data["levels"]) == 2

        # Check first level
        level1 = building_data["levels"][0]
        assert level1["level"] == 1
        assert level1["wood"] == 70
        assert level1["clay"] == 40
        assert level1["iron"] == 60
        assert level1["crop"] == 20
        assert level1["time"] == 186  # 3:06 in seconds
        assert level1["population"] == 2

        # Check second level
        level2 = building_data["levels"][1]
        assert level2["level"] == 2
        assert level2["wood"] == 90
        assert level2["clay"] == 50
        assert level2["iron"] == 75
        assert level2["crop"] == 25
        assert level2["time"] == 276  # 4:36 in seconds
        assert level2["population"] == 1

    def test_parse_building_levels_missing_table(self):
        """Test error handling when building level table is missing."""
        html_content = "<div>No building table here</div>"
        soup = BeautifulSoup(html_content, 'html.parser')

        with pytest.raises(ValueError, match="Building level table not found"):
            parse_building_levels(soup)

    def test_parse_building_levels_missing_header(self):
        """Test error handling when building level header is missing."""
        html_content = """
        <div class="buildingLevelTable">
            <div>No header here</div>
        </div>
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        with pytest.raises(ValueError, match="Building level header not found"):
            parse_building_levels(soup)

    def test_parse_building_levels_no_valid_columns(self):
        """Test error handling when no valid header columns are found."""
        html_content = """
        <div class="buildingLevelTable">
            <div class="buildingLevelHeader buildingLevelRow">
                <div>No grid-area style</div>
            </div>
        </div>
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        with pytest.raises(ValueError, match="No valid header columns found"):
            parse_building_levels(soup)

    def test_parse_building_levels_with_building_name_parameter(self):
        """Test parsing with explicitly provided building name."""
        html_content = """
        <div class="buildingLevelTable">
            <div class="buildingLevelHeader buildingLevelRow">
                <div style="grid-area: lvl;">Level</div>
                <div style="grid-area: r1;">
                    <div class="bt-with-tooltip">
                        <i class="travianImageMisc version-4 size-24 icon-wood"></i>
                    </div>
                </div>
            </div>
            <div class="buildingLevelRow buildingLevelRowData">
                <div class="valueWithIcon" style="grid-area: lvl;">1</div>
                <div class="valueWithIcon" style="grid-area: r1;">100</div>
            </div>
        </div>
        <i class="travianBuildingImage version-4 size-32 tribe-1 building_g1"></i>
        """

        soup = BeautifulSoup(html_content, 'html.parser')
        result = parse_building_levels(soup, "Custom Building Name")

        assert len(result) == 1
        assert result[0]["building_name"] == "Custom Building Name"
        assert result[0]["building_id"] == "g1"


class TestDetermineDataTypeFromClasses:
    """Test cases for the _determine_data_type_from_classes function."""

    def test_resource_types(self):
        """Test identification of resource types."""
        assert _determine_data_type_from_classes(["icon-wood"]) == "wood"
        assert _determine_data_type_from_classes(["icon-clay"]) == "clay"
        assert _determine_data_type_from_classes(["icon-iron"]) == "iron"
        assert _determine_data_type_from_classes(["icon-crop"]) == "crop"

    def test_other_types(self):
        """Test identification of other data types."""
        assert _determine_data_type_from_classes(["icon-time"]) == "time"
        assert _determine_data_type_from_classes(["icon-population"]) == "population"
        assert _determine_data_type_from_classes(["icon-culturePoints"]) == "culture_points"
        assert _determine_data_type_from_classes(["allResources"]) == "total_resources"

    def test_unknown_types(self):
        """Test handling of unknown types."""
        result = _determine_data_type_from_classes(["unknown-class"])
        assert "unknown-class" in result

    def test_string_input(self):
        """Test with string input instead of list."""
        assert _determine_data_type_from_classes("icon-wood") == "wood"


class TestParseLevelRow:
    """Test cases for the _parse_level_row function."""

    def test_parse_level_row_valid(self):
        """Test parsing a valid level row."""
        html_content = """
        <div class="buildingLevelRow buildingLevelRowData">
            <div style="grid-area: lvl;">5</div>
            <div style="grid-area: r1;">1,000</div>
            <div style="grid-area: r2;">800</div>
            <div style="grid-area: time;">01:23:45</div>
            <div style="grid-area: pop;">+3</div>
        </div>
        """

        soup = BeautifulSoup(html_content, 'html.parser')
        row = soup.find("div", class_="buildingLevelRow")
        header_columns = {
            "lvl": "level",
            "r1": "wood",
            "r2": "clay",
            "time": "time",
            "pop": "population"
        }

        result = _parse_level_row(row, header_columns)

        assert result is not None
        assert result["level"] == 5
        assert result["wood"] == 1000  # Comma should be removed
        assert result["clay"] == 800
        assert result["time"] == 5025  # 1:23:45 in seconds
        assert result["population"] == 3  # + sign should be removed

    def test_parse_level_row_missing_level(self):
        """Test that row without level returns None."""
        html_content = """
        <div class="buildingLevelRow buildingLevelRowData">
            <div style="grid-area: r1;">100</div>
        </div>
        """

        soup = BeautifulSoup(html_content, 'html.parser')
        row = soup.find("div", class_="buildingLevelRow")
        header_columns = {"r1": "wood"}

        result = _parse_level_row(row, header_columns)
        assert result is None


class TestParseTimeValue:
    """Test cases for the _parse_time_value function."""

    def test_hms_format(self):
        """Test HH:MM:SS time format."""
        assert _parse_time_value("01:23:45") == 5025
        assert _parse_time_value("00:03:06") == 186
        assert _parse_time_value("10:00:00") == 36000

    def test_numeric_format(self):
        """Test numeric time format."""
        assert _parse_time_value("300") == 300
        assert _parse_time_value("1234") == 1234

    def test_empty_or_invalid(self):
        """Test empty or invalid time values."""
        assert _parse_time_value("") == 0
        assert _parse_time_value(None) == 0
        assert _parse_time_value("invalid") == 0

    def test_mixed_format(self):
        """Test mixed format with other text."""
        assert _parse_time_value("Time: 123 seconds") == 123
        assert _parse_time_value("00:05:30 (fast)") == 330


class TestExtractBuildingId:
    """Test cases for the _extract_building_id function."""

    def test_extract_building_id_valid(self):
        """Test extraction of valid building ID."""
        html_content = '<i class="travianBuildingImage building_g15 size-32"></i>'
        soup = BeautifulSoup(html_content, 'html.parser')

        result = _extract_building_id(soup)
        assert result == "g15"

    def test_extract_building_id_missing(self):
        """Test handling when building ID is missing."""
        html_content = '<div>No building image here</div>'
        soup = BeautifulSoup(html_content, 'html.parser')

        result = _extract_building_id(soup)
        assert result == "unknown"


class TestResourcesScraper:
    """Test cases for the ResourcesScraper class methods."""

    def test_convert_to_building_data_valid(self):
        """Test conversion of raw data to BuildingData model."""
        scraper = ResourcesScraper()
        raw_data = {
            "building_name": "Test Building",
            "building_id": "g1",
            "levels": [
                {
                    "level": 1,
                    "wood": 100,
                    "clay": 80,
                    "iron": 60,
                    "crop": 40,
                    "time": 300,
                    "population": 2,
                    "culture_points": 1
                },
                {
                    "level": 2,
                    "wood": 150,
                    "clay": 120,
                    "iron": 90,
                    "crop": 60,
                    "time": 450,
                    "population": 1,
                    "culture_points": 1
                }
            ]
        }

        result = scraper._convert_to_building_data(raw_data)

        assert isinstance(result, BuildingData)
        assert result.building_name == "Test Building"
        assert result.building_id == "g1"
        assert result.category == "Resources"  # g1 is woodcutter
        assert result.max_level == 2
        assert len(result.levels) == 2

        # Check first level
        level1 = result.levels[0]
        assert isinstance(level1, BuildingLevel)
        assert level1.level == 1
        assert isinstance(level1.resource_cost, ResourceCosts)
        assert level1.resource_cost.wood == 100
        assert level1.resource_cost.clay == 80
        assert level1.resource_cost.iron == 60
        assert level1.resource_cost.crop == 40
        assert level1.build_time == 300
        assert level1.population == 2
        assert level1.culture_points == 1

    def test_convert_to_building_data_no_levels(self):
        """Test error handling when no level data is provided."""
        scraper = ResourcesScraper()
        raw_data = {
            "building_name": "Test Building",
            "building_id": "g1",
            "levels": []
        }

        with pytest.raises(ValueError, match="No level data found"):
            scraper._convert_to_building_data(raw_data)

    def test_determine_building_category(self):
        """Test building category determination."""
        scraper = ResourcesScraper()

        # Test resource buildings
        assert scraper._determine_building_category("g1", "Woodcutter") == "Resources"
        assert scraper._determine_building_category("g2", "Clay Pit") == "Resources"

        # Test military buildings
        assert scraper._determine_building_category("g19", "Barracks") == "Military"
        assert scraper._determine_building_category("g20", "Stable") == "Military"

        # Test infrastructure (default)
        assert scraper._determine_building_category("g15", "Main Building") == "Infrastructure"
        assert scraper._determine_building_category("unknown", "Unknown Building") == "Infrastructure"


class TestResourceCosts:
    """Test cases for the ResourceCosts model."""

    def test_resource_costs_creation(self):
        """Test creation of ResourceCosts object."""
        costs = ResourceCosts(wood=100, clay=80, iron=60, crop=40)

        assert costs.wood == 100
        assert costs.clay == 80
        assert costs.iron == 60
        assert costs.crop == 40
        assert costs.total == 280

    def test_resource_costs_validation(self):
        """Test validation of ResourceCosts values."""
        # Valid values
        ResourceCosts(wood=0, clay=0, iron=0, crop=0)
        ResourceCosts(wood=1000, clay=2000, iron=3000, crop=4000)

        # Invalid values should raise validation error
        with pytest.raises(ValueError):
            ResourceCosts(wood=-1, clay=0, iron=0, crop=0)


class TestBuildingLevel:
    """Test cases for the BuildingLevel model."""

    def test_building_level_creation(self):
        """Test creation of BuildingLevel object."""
        resource_cost = ResourceCosts(wood=100, clay=80, iron=60, crop=40)
        level = BuildingLevel(
            level=5,
            resource_cost=resource_cost,
            build_time=300,
            population=2,
            culture_points=1
        )

        assert level.level == 5
        assert level.resource_cost == resource_cost
        assert level.build_time == 300
        assert level.population == 2
        assert level.culture_points == 1

    def test_building_level_validation(self):
        """Test validation of BuildingLevel values."""
        resource_cost = ResourceCosts(wood=100, clay=80, iron=60, crop=40)

        # Valid values
        BuildingLevel(level=1, resource_cost=resource_cost, build_time=0, population=0, culture_points=0)
        BuildingLevel(level=25, resource_cost=resource_cost, build_time=10000, population=100, culture_points=10)

        # Invalid level should raise validation error
        with pytest.raises(ValueError):
            BuildingLevel(level=0, resource_cost=resource_cost, build_time=0, population=0, culture_points=0)

        with pytest.raises(ValueError):
            BuildingLevel(level=26, resource_cost=resource_cost, build_time=0, population=0, culture_points=0)


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_full_parsing_workflow(self):
        """Test the complete parsing workflow with realistic JavaScript-rendered HTML."""
        html_content = """
        <html>
        <body>
            <div class="buildingTitle">Woodcutter</div>
            <i class="travianBuildingImage version-4 size-32 tribe-1 building_g1"></i>
            <div class="buildingLevelTable effectCount1">
                <div class="buildingLevelHeader buildingLevelRow">
                    <div style="grid-area: lvl;">Level</div>
                    <div style="grid-area: r1;">
                        <div class="bt-with-tooltip">
                            <i class="travianImageMisc version-4 size-24 icon-wood"></i>
                        </div>
                    </div>
                    <div style="grid-area: r2;">
                        <div class="bt-with-tooltip">
                            <i class="travianImageMisc version-4 size-24 icon-clay"></i>
                        </div>
                    </div>
                    <div style="grid-area: time;">
                        <div class="bt-with-tooltip">
                            <i class="travianImageMisc version-4 size-24 icon-time"></i>
                        </div>
                    </div>
                    <div style="grid-area: pop;">
                        <div class="bt-with-tooltip">
                            <i class="travianImageMisc version-4 size-24 icon-population"></i>
                        </div>
                    </div>
                </div>
                <div class="buildingLevelRow buildingLevelRowData">
                    <div class="valueWithIcon" style="grid-area: lvl;">1</div>
                    <div class="valueWithIcon" style="grid-area: r1;">40</div>
                    <div class="valueWithIcon" style="grid-area: r2;">100</div>
                    <div class="valueWithIcon" style="grid-area: time;">00:04:20</div>
                    <div class="valueWithIcon" style="grid-area: pop;">1</div>
                </div>
            </div>
        </body>
        </html>
        """

        soup = BeautifulSoup(html_content, 'html.parser')
        result = parse_building_levels(soup)

        # Verify the complete workflow
        assert len(result) == 1
        building_data = result[0]
        assert building_data["building_name"] == "Woodcutter"
        assert building_data["building_id"] == "g1"
        assert len(building_data["levels"]) == 1

        level_data = building_data["levels"][0]
        assert level_data["level"] == 1
        assert level_data["wood"] == 40
        assert level_data["clay"] == 100
        assert level_data["time"] == 260  # 4:20 in seconds
        assert level_data["population"] == 1

        # Test conversion to structured model
        scraper = ResourcesScraper()
        structured_data = scraper._convert_to_building_data(building_data)

        assert isinstance(structured_data, BuildingData)
        assert structured_data.building_name == "Woodcutter"
        assert structured_data.category == "Resources"
        assert len(structured_data.levels) == 1


class TestBuildingEffects:
    """Test cases for building effects extraction and parsing."""

    def test_parse_effect_value_percentage(self):
        """Test parsing percentage effect values."""
        # Test crop bonus percentage
        assert parse_effect_value("+25%", "production_bonus") == 25.0
        assert parse_effect_value("+5%", "production_bonus") == 5.0
        assert parse_effect_value("15%", "production_bonus") == 15.0

        # Test training time reduction (special case)
        assert parse_effect_value("90.0%", "training_time_reduction") == 10.0  # 90% time = 10% reduction
        assert parse_effect_value("81.0%", "training_time_reduction") == 19.0
        assert parse_effect_value("100.0%", "training_time_reduction") == 0.0

    def test_parse_effect_value_absolute(self):
        """Test parsing absolute effect values."""
        # Test storage capacity
        assert parse_effect_value("1,200", "storage_capacity") == 1200
        assert parse_effect_value("5,000", "storage_capacity") == 5000
        assert parse_effect_value("80,000", "storage_capacity") == 80000

        # Test population bonus
        assert parse_effect_value("100", "population_bonus") == 100
        assert parse_effect_value("500", "population_bonus") == 500

    def test_parse_effect_value_invalid(self):
        """Test parsing invalid effect values."""
        assert parse_effect_value("", "production_bonus") is None
        assert parse_effect_value("invalid", "storage_capacity") is None
        assert parse_effect_value(None, "training_time_reduction") is None

    def test_categorize_effect_by_icon(self):
        """Test categorizing effects by icon class."""
        assert categorize_effect_by_icon(["icon-cropBonus"]) == "production_bonus"
        assert categorize_effect_by_icon(["icon-warehouseCap"]) == "storage_capacity"
        assert categorize_effect_by_icon(["icon-infantryBonusTime"]) == "training_time_reduction"
        assert categorize_effect_by_icon(["icon-unknown"]) is None

    def test_get_effect_type_from_icon(self):
        """Test getting effect type information from icon."""
        effect_info = get_effect_type_from_icon("icon-cropBonus")
        assert effect_info is not None
        assert effect_info["type"] == "production_bonus"
        assert effect_info["category"] == "production"
        assert effect_info["unit"] == "percentage"

        warehouse_info = get_effect_type_from_icon("icon-warehouseCap")
        assert warehouse_info is not None
        assert warehouse_info["type"] == "storage_capacity"
        assert warehouse_info["unit"] == "absolute"

    def test_building_effects_with_storage_capacity(self):
        """Test parsing building with storage capacity effect (like Warehouse)."""
        html_content = """
        <html>
        <body>
            <div class="buildingLevelTable effectCount1">
                <div class="buildingLevelHeader buildingLevelRow">
                    <div style="grid-area: lvl;">Level</div>
                    <div style="grid-area: r1;"><div class="bt-with-tooltip"><i class="icon-wood"></i></div></div>
                    <div style="grid-area: r2;"><div class="bt-with-tooltip"><i class="icon-clay"></i></div></div>
                    <div style="grid-area: r3;"><div class="bt-with-tooltip"><i class="icon-iron"></i></div></div>
                    <div style="grid-area: r4;"><div class="bt-with-tooltip"><i class="icon-crop"></i></div></div>
                    <div style="grid-area: f0;"><div class="bt-with-tooltip"><i class="icon-warehouseCap"></i></div></div>
                </div>
                <div class="buildingLevelRow buildingLevelRowData">
                    <div style="grid-area: lvl;">1</div>
                    <div style="grid-area: r1;">130</div>
                    <div style="grid-area: r2;">160</div>
                    <div style="grid-area: r3;">90</div>
                    <div style="grid-area: r4;">40</div>
                    <div style="grid-area: f0;">1,200</div>
                </div>
            </div>
            <div class="buildingTitle">Warehouse</div>
            <i class="building_g10"></i>
        </body>
        </html>
        """

        soup = BeautifulSoup(html_content, 'html.parser')
        result = parse_building_levels(soup)

        assert len(result) == 1
        building_data = result[0]
        assert len(building_data["levels"]) == 1

        level_data = building_data["levels"][0]
        assert "storage_capacity" in level_data
        assert level_data["storage_capacity"] == 1200

    def test_building_effects_with_production_bonus(self):
        """Test parsing building with production bonus (like Bakery)."""
        html_content = """
        <html>
        <body>
            <div class="buildingLevelTable effectCount1">
                <div class="buildingLevelHeader buildingLevelRow">
                    <div style="grid-area: lvl;">Level</div>
                    <div style="grid-area: r1;"><div class="bt-with-tooltip"><i class="icon-wood"></i></div></div>
                    <div style="grid-area: r2;"><div class="bt-with-tooltip"><i class="icon-clay"></i></div></div>
                    <div style="grid-area: r3;"><div class="bt-with-tooltip"><i class="icon-iron"></i></div></div>
                    <div style="grid-area: r4;"><div class="bt-with-tooltip"><i class="icon-crop"></i></div></div>
                    <div style="grid-area: f0;"><div class="bt-with-tooltip"><i class="icon-cropBonus"></i></div></div>
                </div>
                <div class="buildingLevelRow buildingLevelRowData">
                    <div style="grid-area: lvl;">1</div>
                    <div style="grid-area: r1;">1200</div>
                    <div style="grid-area: r2;">1480</div>
                    <div style="grid-area: r3;">870</div>
                    <div style="grid-area: r4;">1600</div>
                    <div style="grid-area: f0;">+5%</div>
                </div>
            </div>
            <div class="buildingTitle">Bakery</div>
            <i class="building_g9"></i>
        </body>
        </html>
        """

        soup = BeautifulSoup(html_content, 'html.parser')
        result = parse_building_levels(soup)

        assert len(result) == 1
        building_data = result[0]
        assert len(building_data["levels"]) == 1

        level_data = building_data["levels"][0]
        assert "production_bonus" in level_data
        assert level_data["production_bonus"] == 5.0

    def test_building_effects_with_training_time_reduction(self):
        """Test parsing building with training time reduction (like Barracks)."""
        html_content = """
        <html>
        <body>
            <div class="buildingLevelTable effectCount1">
                <div class="buildingLevelHeader buildingLevelRow">
                    <div style="grid-area: lvl;">Level</div>
                    <div style="grid-area: r1;"><div class="bt-with-tooltip"><i class="icon-wood"></i></div></div>
                    <div style="grid-area: r2;"><div class="bt-with-tooltip"><i class="icon-clay"></i></div></div>
                    <div style="grid-area: r3;"><div class="bt-with-tooltip"><i class="icon-iron"></i></div></div>
                    <div style="grid-area: r4;"><div class="bt-with-tooltip"><i class="icon-crop"></i></div></div>
                    <div style="grid-area: f0;"><div class="bt-with-tooltip"><i class="icon-infantryBonusTime"></i></div></div>
                </div>
                <div class="buildingLevelRow buildingLevelRowData">
                    <div style="grid-area: lvl;">2</div>
                    <div style="grid-area: r1;">270</div>
                    <div style="grid-area: r2;">180</div>
                    <div style="grid-area: r3;">335</div>
                    <div style="grid-area: r4;">155</div>
                    <div style="grid-area: f0;">90.0%</div>
                </div>
            </div>
            <div class="buildingTitle">Barracks</div>
            <i class="building_g19"></i>
        </body>
        </html>
        """

        soup = BeautifulSoup(html_content, 'html.parser')
        result = parse_building_levels(soup)

        assert len(result) == 1
        building_data = result[0]
        assert len(building_data["levels"]) == 1

        level_data = building_data["levels"][0]
        assert "training_time_reduction" in level_data
        assert level_data["training_time_reduction"] == 10.0  # 90% time = 10% reduction


class TestBuildingEffectsModel:
    """Test cases for the BuildingEffects model."""

    def test_building_effects_creation(self):
        """Test creating BuildingEffects with various effect types."""
        effects = BuildingEffects(
            storage_capacity=1200,
            production_bonus={"crop": 5.0},
            training_time_reduction=10.0
        )

        assert effects.storage_capacity == 1200
        assert effects.production_bonus == {"crop": 5.0}
        assert effects.training_time_reduction == 10.0
        assert effects.has_effects is True

    def test_building_effects_empty(self):
        """Test empty BuildingEffects."""
        effects = BuildingEffects()
        assert effects.has_effects is False
        assert effects.get_effect_summary() == {}

    def test_building_effects_summary(self):
        """Test building effects summary."""
        effects = BuildingEffects(
            storage_capacity=5000,
            offensive_bonus=15.0,
            other_effects={"special_ability": "increased_range"}
        )

        summary = effects.get_effect_summary()
        assert summary["storage_capacity"] == 5000
        assert summary["offensive_bonus"] == 15.0
        assert summary["other_effects"] == {"special_ability": "increased_range"}


class TestBuildingEffectsIntegration:
    """Integration tests for building effects extraction."""

    def test_convert_to_building_data_with_effects(self):
        """Test converting raw data with effects to BuildingData."""
        raw_data = {
            "building_name": "Warehouse",
            "building_id": "g10",
            "levels": [
                {
                    "level": 1,
                    "wood": 130,
                    "clay": 160,
                    "iron": 90,
                    "crop": 40,
                    "time": 2000,
                    "population": 1,
                    "culture_points": 1,
                    "storage_capacity": 1200
                },
                {
                    "level": 2,
                    "wood": 165,
                    "clay": 205,
                    "iron": 115,
                    "crop": 50,
                    "time": 2620,
                    "population": 2,
                    "culture_points": 1,
                    "storage_capacity": 1700
                }
            ]
        }

        scraper = ResourcesScraper()
        building_data = scraper._convert_to_building_data(raw_data)

        assert isinstance(building_data, BuildingData)
        assert building_data.building_name == "Warehouse"
        assert len(building_data.levels) == 2

        # Check first level effects
        level1 = building_data.levels[0]
        assert level1.effects is not None
        assert level1.effects.storage_capacity == 1200
        assert level1.effects.has_effects is True

        # Check second level effects
        level2 = building_data.levels[1]
        assert level2.effects is not None
        assert level2.effects.storage_capacity == 1700

    def test_extract_level_effects_method(self):
        """Test the _extract_level_effects method directly."""
        scraper = ResourcesScraper()

        # Test with storage capacity effect
        level_data_warehouse = {
            "level": 1,
            "wood": 130,
            "storage_capacity": 1200
        }

        effects = scraper._extract_level_effects(level_data_warehouse, "g10")
        assert effects is not None
        assert effects.storage_capacity == 1200

        # Test with production bonus effect
        level_data_bakery = {
            "level": 1,
            "wood": 1200,
            "production_bonus": 5.0
        }

        effects = scraper._extract_level_effects(level_data_bakery, "g9")
        assert effects is not None
        assert effects.production_bonus == {"general": 5.0}

        # Test with no effects
        level_data_no_effects = {
            "level": 1,
            "wood": 40,
            "clay": 100
        }

        effects = scraper._extract_level_effects(level_data_no_effects, "g1")
        assert effects is None