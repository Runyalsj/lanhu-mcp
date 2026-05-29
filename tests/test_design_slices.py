from lanhu_mcp_server import LanhuExtractor


def _make_extractor():
    return object.__new__(LanhuExtractor)


def test_extract_slices_from_dds_schema_finds_nested_images():
    extractor = _make_extractor()
    schema = {
        "layers": [
            {
                "id": "group-1",
                "name": "礼物栏",
                "type": "group",
                "children": [
                    {
                        "id": "slice-1",
                        "name": "TOP2",
                        "type": "bitmapLayer",
                        "frame": {"x": 12, "y": 34, "width": 120, "height": 66},
                        "image": {
                            "imageUrl": "https://cdn.example.com/top2.png",
                            "svgUrl": "https://cdn.example.com/top2.svg",
                            "size": {"width": 120, "height": 66},
                        },
                    }
                ],
            }
        ]
    }

    slices = extractor._extract_slices_from_dds_schema(
        schema,
        include_metadata=True,
        slice_scale=2,
    )

    assert len(slices) == 2
    png_slice = next(s for s in slices if s["download_url"].endswith(".png"))
    assert png_slice["name"] == "TOP2"
    assert png_slice["layer_path"] == "礼物栏/TOP2"
    assert png_slice["logical_size"]["width"] == 120
    assert png_slice["scale_urls"]["2x"] == "https://cdn.example.com/top2.png"
    assert png_slice["metadata"]["source"] == "dds_schema"


def test_extract_slices_from_dds_schema_reads_images_dict_and_dedupes():
    extractor = _make_extractor()
    schema = {
        "items": [
            {
                "id": "slice-2",
                "name": "独角兽",
                "type": "symbolInstance",
                "bounds": {"left": 2, "top": 4, "width": 48, "height": 48},
                "images": {
                    "png_xxxhd": "https://cdn.example.com/unicorn.png",
                    "svg": "https://cdn.example.com/unicorn.svg",
                },
            },
            {
                "id": "slice-2",
                "name": "独角兽",
                "type": "symbolInstance",
                "bounds": {"left": 2, "top": 4, "width": 48, "height": 48},
                "images": {
                    "png_xxxhd": "https://cdn.example.com/unicorn.png",
                    "svg": "https://cdn.example.com/unicorn.svg",
                },
            },
        ]
    }

    slices = extractor._extract_slices_from_dds_schema(
        schema,
        include_metadata=False,
        slice_scale=2,
    )

    assert len(slices) == 1
    assert slices[0]["download_url"] == "https://cdn.example.com/unicorn.png"
    assert slices[0]["position"] == {"x": 2, "y": 4}
