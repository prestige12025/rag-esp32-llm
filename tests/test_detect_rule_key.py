from app import detect_rule_key


def test_detect_i2c_spi():
    q = "ESP32 I2C and SPI communication example"
    assert detect_rule_key(q) == "i2c_spi"


def test_detect_i2c_only():
    q = "ESP32 I2C sensor example"
    assert detect_rule_key(q) == "i2c"


def test_detect_spi_only():
    q = "ESP32 SPI display driver"
    assert detect_rule_key(q) == "spi"


def test_detect_default():
    q = "ESP32 GPIO interrupt example"
    assert detect_rule_key(q) == "default"


def test_detect_case_insensitive():
    q = "Esp32 I2c Test"
    assert detect_rule_key(q) == "i2c"


def test_detect_keyword_order_independent():
    q = "SPI and I2C both used here"
    assert detect_rule_key(q) == "i2c_spi"
