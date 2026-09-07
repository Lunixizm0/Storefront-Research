if __name__ == "__main__":
    import json

    from scrape.dataset import ProductDataset
    from scrape.utils import mediamarkt

    url = "https://www.mediamarkt.com.tr/tr/product/_dyson-v15-detect-kablosuz-sarjli-dikey-supurge-sari-nikel-1232522.html"
    response = mediamarkt.get_raw_html(url)
    soup = mediamarkt.parse_html(response.content)
    dataset = mediamarkt.extract_product_dataset(soup, url=url)
    if isinstance(dataset, ProductDataset):
        print(json.dumps(dataset.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(dataset, ensure_ascii=False, indent=2))
