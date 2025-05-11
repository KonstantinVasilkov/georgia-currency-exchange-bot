from src.bot.routers.currency import (
    generate_google_maps_multi_pin_url,
    generate_apple_maps_multi_pin_url,
)


class MockOffice:
    def __init__(self, lat: float, lng: float) -> None:
        self.lat = lat
        self.lng = lng


def test_generate_google_maps_multi_pin_url_empty() -> None:
    assert generate_google_maps_multi_pin_url([]) == "https://maps.google.com/"


def test_generate_google_maps_multi_pin_url_multiple() -> None:
    offices = [MockOffice(41.7151, 44.8271), MockOffice(41.7200, 44.8000)]
    url = generate_google_maps_multi_pin_url(offices)
    assert url.startswith("https://www.google.com/maps/dir/")
    assert "41.7151,44.8271" in url
    assert "41.7200,44.8000" in url


def test_generate_apple_maps_multi_pin_url_empty() -> None:
    assert generate_apple_maps_multi_pin_url([]) == "http://maps.apple.com/"


def test_generate_apple_maps_multi_pin_url_multiple() -> None:
    offices = [MockOffice(41.7151, 44.8271), MockOffice(41.7200, 44.8000)]
    url = generate_apple_maps_multi_pin_url(offices)
    assert url.startswith("http://maps.apple.com/?")
    assert "q=41.7151,44.8271" in url
    assert "q=41.7200,44.8000" in url
