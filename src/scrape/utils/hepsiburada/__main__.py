if __name__ == "__main__":
    import json

    from scrape.dataset import ProductDataset
    from scrape.utils import hepsiburada

    url = "https://www.hepsiburada.com/karaca-tea-break-inox-siyah-celik-su-isitici-cay-makinesi-pm-HBC00002JH1M2"
    dataset = hepsiburada.extract_product_dataset(url)
    if isinstance(dataset, ProductDataset):
        print(json.dumps(dataset.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(dataset, ensure_ascii=False, indent=2))
