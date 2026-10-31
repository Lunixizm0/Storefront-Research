# Trendyol Kredi Teklifleri

Retrieves calculated monthly installment (taksit) payment options for a given price from Trendyol's consumer lending (Kredi Teklifleri) service. The response lists available banks along with their loan terms, monthly payment amounts, interest rates, and annual effective interest rates.

## Endpoint

```
GET https://coc-webview.trendyol.com/api/p/monthly-payments/calculated
```

## Query Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `price` | number | Yes | The total purchase price for which loan offers are calculated (e.g. `10000.0`). |
| `maxTerm` | number | Yes | The maximum installment term (in months) to include in results. Use a large value like `99999` to retrieve all available terms. |
| `bankCategoryId` | number | NO | The category ID of the bank type to filter results. `13` corresponds to participation (Islamic) banks. |

## Request Headers

| Header | Description |
| --- | --- |
| `User-Agent` | Browser user-agent string used to identify the client. |
| `Cookie` | Session/preference cookies including `platform`, `countryCode`, and `language`. |

## Response

Returns a JSON object with a `monthlyPayments` array. Each element represents a bank and contains:

- **`bank`** - Bank details: `id`, `name`, `type` (e.g. `PARTICIPATION`), and `logo` URL.

- **`monthlyPaymentRates`** - Array of installment plans, each with:
    - `term` - Number of monthly installments.

    - `interestRate` - Monthly interest rate (%).

    - `amount` - Monthly payment amount (TRY).

    - `totalPaymentAmount` - Total amount to be paid over all terms (TRY).

    - `annualEffectiveInterestRate` - Annual effective interest rate (%).

    - `type` - Loan type (e.g. `CONSUMER_LOAN`).

    - `highlight` - Whether this plan is highlighted/recommended.

## Notes

Server returns HTTP 500 when i delete 'price' or 'maxTerm' parameters. No issues when i tried to delete 'bankCategoryId'
Might be lead to something.

**HTTP 500 Response**

``` json
{
  "source": "CONSUMERLENDING_BFF",
  "title": "UNKNOWN",
  "message": "We are currently unable to complete your request."
}
```
## Example

**Request:**

```
GET https://coc-webview.trendyol.com/api/p/monthly-payments/calculated?price=10000.0&maxTerm=99999&bankCategoryId=13
```

**Response (excerpt):**

``` json
{
  "monthlyPayments": [
    {
      "bank": {
        "id": "BANK:TURKIYEFINANS",
        "name": "Türkiye Finans",
        "type": "PARTICIPATION"
      },
      "monthlyPaymentRates": [
        {
          "term": 3,
          "interestRate": 2.95,
          "amount": 3593.0,
          "totalPaymentAmount": 10779.0,
          "annualEffectiveInterestRate": 57.08,
          "type": "CONSUMER_LOAN",
          "highlight": true
        }
      ]
    }
  ]
}
```
