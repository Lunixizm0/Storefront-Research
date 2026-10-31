# Ürün Yorumları ve Puan Özeti

Retrieves the product reviews, an AI-generated summary, and aggregate rating statistics for a product on the Trendyol storefront. This is one of the richest endpoints: it returns the average rating, rating distribution (1-5 stars), review tags with sentiment analysis, and the actual review entries (pagination supported).

## Endpoint

```
GET https://apigw.trendyol.com/discovery-storefront-trproductgw-service/api/review-read/product-reviews/detailed
```

## Query Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `contentId` | number | Yes | The unique product identifier (e.g. `1081766367`). |
| `page` | number | NO | Zero-based page index of the reviews to fetch (e.g. `0`). |
| `pageSize` | number | NO | Number of reviews per page (e.g. `5`; larger values like `10`/`20` are accepted). |
| `channelId` | number | NO | The sales channel identifier. Use `1` for the web channel. |

## Request Headers

Mimic a browser request; the `x-agentname` / `x-web-req-source` / `Origin` combination together with a `csrf-secret` cookie is what bypasses the storefront gateway anti-bot checks (tested successfully with plain `requests`):

| Header | Required | Description |
| --- | --- | --- |
| `User-Agent` | Yes | Browser user-agent string. |
| `Accept` | No | `application/json, text/plain, */*` |
| `Accept-Language` | No | e.g. `tr-TR,tr;q=0.9,en-US;q=0.8` |
| `x-agentname` | No | `StorefrontProductGateway` |
| `x-web-req-source` | No | `StorefrontProductGateway` |
| `Origin` | No | `https://www.trendyol.com` |
| `Cookie` | | `platform=web; AZ_SELECTED=false; storefrontId=1; countryCode=TR; language=tr; csrf-secret=...` |

## Response

Top-level wrapper: `{ "isSuccess", "statusCode", "result" }`. The `result` object contains:

- **`aiSummary`** - String. AI-generated bullet summary of what reviewers commonly praise/criticize.

- **`summary`** - Object with aggregate rating data:
    - `averageRating` / `averageRatingFixed` - average rating (e.g. `4.3`).

    - `countries` - array of `{ country, reviewsExist }`.

    - `totalRatingCount` - total number of ratings.

    - `totalCommentCount` - total number of text comments.

    - `totalPages` - total pagination pages (derived from pageSize).

    - `hasMediaFiles` / `totalImageReviewCount` - whether photo/video reviews exist and how many.

    - `ratingCounts` - array of `{ rate, count }` (1..5 star distribution).

    - `tags` - array of review tags; each has `name`, `count`, optional `sentiment: { positive, negative, ratio }`, and optional `imageUrl`.

- **`reviews`** - Array of review objects, each with:
    - `id` - review id.

    - `contentId` - product id.

    - `userFullName` / `showUserFullName` - user name (usually masked as `**** ****`).

    - `isElite`, `isInfluencer` - flags.

    - `seller` - `{ id, name }` of the selling merchant.

    - `rate` - star rating (1-5).

    - `comment` - review text.

    - `likesCount` - number of likes.

    - `language` - e.g. `tr`.

    - `createdAt` / `lastModifiedAt` - epoch millis timestamps.

    - `mediaFiles` - array of `{ id, url, thumbnailUrl, mediaType, height, weight }` for attached photos/videos.

    - `trusted` - boolean; verified purchase flag.

    - `culture`, `sourceChannelId`.

## Example

**Request:**

```
GET https://apigw.trendyol.com/discovery-storefront-trproductgw-service/api/review-read/product-reviews/detailed?contentId=1081766367&page=0&pageSize=5&channelId=1
```

**Response (excerpt):**

``` json
{
  "isSuccess": true,
  "statusCode": 200,
  "result": {
    "aiSummary": "• Birçok yorumda ses kalitesi, özellikle netlik, dengeli baslar ve yüksek ses seviyesi övgüyle karşılanıyor.",
    "summary": {
      "averageRating": 4.3,
      "averageRatingFixed": "4.3",
      "totalRatingCount": 102,
      "totalCommentCount": 53,
      "totalPages": 11,
      "totalImageReviewCount": 12,
      "ratingCounts": [
        { "rate": 5, "count": 72 },
        { "rate": 4, "count": 10 },
        { "rate": 3, "count": 9 },
        { "rate": 2, "count": 4 },
        { "rate": 1, "count": 7 }
      ],
      "tags": [
        { "name": "fotoğraflı", "count": 12 },
        { "name": "Ses Özellikleri", "count": 23, "sentiment": { "positive": 17, "negative": 6, "ratio": 74 } }
      ]
    },
    "reviews": [
      {
        "id": 618137832,
        "contentId": 1081766367,
        "userFullName": "**** ****",
        "seller": { "id": 984136, "name": "Xiaomi Resmi Mağazası" },
        "rate": 5,
        "comment": "Yeni kulaklık oldukça iyi ayrıca istediğim renkte de geldi",
        "likesCount": 0,
        "trusted": true,
        "mediaFiles": [{ "mediaType": "IMAGE", "thumbnailUrl": "..." }]
      }
    ]
  }
}
```
