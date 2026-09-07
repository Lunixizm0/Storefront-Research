if __name__ == "__main__":
    import json

    from scrape.dataset import ProductDataset
    from scrape.utils import trendyol

    url = "https://www.trendyol.com/xiaomi/redmi-buds-8-pro-siyah-bluetooth-kulakici-kulaklik-tws-anc-bt-5-4-xiaomi-tr-garantili-p-1081766367"
    dataset = trendyol.extract_product_dataset(url)
    if isinstance(dataset, ProductDataset):
        print(json.dumps(dataset.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(dataset, ensure_ascii=False, indent=2))
