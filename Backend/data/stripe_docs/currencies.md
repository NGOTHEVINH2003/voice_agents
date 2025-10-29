# Supported currencies

See what currencies you can use for making charges and for paying out to your bank account.

In the United States, you can accept these cards: Visa, Mastercard, American Express, Discover, JCB, Diners Club, China UnionPay, debit cards.

You can accept a range of other [payment methods](https://docs.stripe.com/payments/payment-methods/payment-method-support.md#country-currency-support), depending on the country of your Stripe account (which you set when you [activate it](https://docs.stripe.com/get-started/account/activate.md#activation)).

You can charge customers in more than [135 currencies](https://docs.stripe.com/currencies.md#presentment-currencies) and [receive funds in your preferred currency](https://docs.stripe.com/payments/currencies/settlement-payouts.md). [Converting prices to local currencies](https://docs.stripe.com/payments/currencies/localize-prices.md) can improve customer conversion and authorization rates, while lowering payment processing costs at the same time.

## Currency presentment and settlement

Currency affects three aspects of Stripe payments:

- The customer’s payment method currency, such as their credit card or bank account
- The currency of the charge, called the *presentment* currency
- The currency accepted by your destination bank account or debit card, called the *settlement* currency

If the charge currency differs from the customer’s payment method currency, their bank or card issuer might charge the *customer* a foreign exchange fee. The bank or card issuer might also charge the customer if the payment method and your business are in different countries, regardless of the currency used.

*Connect* (Connect is Stripe's solution for multi-party businesses, such as marketplace or software platforms, to route payments between sellers, customers, and other recipients) platforms have additional considerations with respect to currency conversions. For more information about managing currency conversions as a Connect platform, see [Work with multiple currencies](https://docs.stripe.com/connect/currencies.md).

If the charge currency differs from your *settlement currency* (The settlement currency is the currency your bank account uses), Stripe converts the charge to your settlement currency, with [multiple options](https://docs.stripe.com/payments/currencies/localize-prices.md) for presenting, converting, and charging customers in different currencies.

In certain countries, Stripe might support [settlement in additional currencies](https://docs.stripe.com/payments/currencies/settlement-payouts.md). If you need liquidity in additional currencies, you can enable settlement in those currencies and add a bank account in your [payout settings of your Dashboard](https://dashboard.stripe.com/account/payouts). Our [payouts documentation](https://docs.stripe.com/payouts.md#multiple-bank-accounts) lists the different bank account currencies we support. See [Stripe pricing](https://www.stripe.com/pricing) for conversion costs.

## Supported presentment currencies 

Currencies shown as links are [zero-decimal](https://docs.stripe.com/currencies.md#zero-decimal) currencies. Additionally, make sure to use all lowercase letters when entering the three-letter ISO code in any payment request.

## Minor units in API amounts 

All API requests expect `amount` values in the *currency’s minor unit* (The Stripe API expects currency values using the given denomination's smallest unit represented without decimals. For example, enter 1099 to charge 10.99 USD (or any other two-decimal currency). Enter 10 to charge 10 JPY (or any other zero-decimal currency)). For example, enter:

- `1000` to charge 10 USD (or any other two-decimal currency).
- `10` to charge 10 JPY (or any other zero-decimal currency).

### Two-decimal currencies 

Currencies are two-decimal currencies unless otherwise specified.

### Zero-decimal currencies 

For the following zero-decimal currencies, the charge and the amount are the same, without requiring multiplication. For example, to charge 500 JPY, provide an `amount` value of `500`.

> This list contains zero-decimal currencies that have general API support. Currencies listed here might not be available in your specific country. For the list of presentment currencies for your country, see [Supported presentment currencies](https://docs.stripe.com/currencies.md#presentment-currencies).

### Special cases 

The following currencies have special conditions that you need to consider when creating payouts or charges.

| Currency                | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Icelandic Króna (ISK)   | ISK transitioned to a zero-decimal currency, but backwards compatibility requires you to represent it as a two-decimal value, where the decimal amount is always `00`. For example, to charge 5 ISK, provide an `amount` value of `500`. You can’t charge fractions of ISK.                                                                                                                                                                                                                                                    |
| Hungarian Forint (HUF)  | Stripe treats HUF as a zero-decimal currency for payouts, even though you can charge two-decimal amounts. When you create a manual payout in HUF, you must provide integer amounts that are evenly divisible by 100. For example, if you have an available balance of HUF 10.45, you can pay out HUF 10 by submitting `1000` for the `amount` value. You can’t submit a payout for the full balance, HUF 10.45, because the `amount` value of `1045` isn’t evenly divisible by 100.                                            |
| New Taiwan Dollar (TWD) | Stripe treats TWD as a zero-decimal currency for payouts, even though you can charge two-decimal amounts. When you create a manual payout in TWD, you must provide integer amounts that are evenly divisible by 100. For example, if you have an available balance of TWD 800.45, you can pay out TWD 800 by submitting `80000` for the `amount` value. You can’t submit a payout for the full balance, TWD 800.45, because the `amount` value of `80045` isn’t evenly divisible by 100.                                       |
| Ugandan Shilling (UGX)  | UGX transitioned to a zero-decimal currency, but backwards compatibility requires you to represent it as a two-decimal value, where the decimal amount is always `00`. For example, to charge 5 UGX, provide an `amount` value of `500`. You can’t charge fractions of UGX. For invoices where the `amount` is fractional after prorations, coupons, or taxes, Stripe automatically rounds that amount to the nearest number evenly divisible by 100. We credit or debit any difference from rounding to the customer balance. |

## Minimum and maximum charge amounts

Stripe enforces a minimum payment amount for all charges to make sure the Stripe fee doesn’t exceed your charge. The minimum amount you can charge depends on the payout [bank account settlement currency](https://docs.stripe.com/payouts.md#supported-accounts-and-settlement-currencies).

Subscription charges support zero-amount charges to account for coupons and free trials. However, any non-zero amount is still subject to the applicable minimum.

| Settlement currency | Minimum charge amount |
| ------------------- | --------------------- |
| USD                 | $0.50                 |
| AED                 | 2.00 د.إ              |
| AUD                 | $0.50                 |
| BGN                 | лв1.00                |
| BRL                 | R$0.50                |
| CAD                 | $0.50                 |
| CHF                 | 0.50 Fr               |
| CZK                 | 15.00Kč               |
| DKK                 | 2.50-kr.              |
| EUR                 | €0.50                 |
| GBP                 | £0.30                 |
| HKD                 | $4.00                 |
| HUF                 | 175.00 Ft             |
| INR                 | ₹0.50                 |
| JPY                 | ¥50                   |
| MXN                 | $10                   |
| MYR                 | RM 2                  |
| NOK                 | 3.00-kr.              |
| NZD                 | $0.50                 |
| PLN                 | 2.00 zł               |
| RON                 | lei2.00               |
| SEK                 | 3.00-kr.              |
| SGD                 | $0.50                 |
| THB                 | ฿10                   |

If you only have one bank account, the minimum amount shown applies to all charges in the same currency as the account. Charges requiring [conversion](https://docs.stripe.com/payments/currencies/localize-prices.md) into your account’s [default settlement currency](https://docs.stripe.com/payouts.md#multiple-bank-accounts) must meet the equivalent minimum of the settlement currency. For example, if you have GBP and USD bank accounts, with GBP set as your default currency, any non-USD charges you create convert to GBP. These charges must meet the minimum amount required for GBP (£0.30) after conversion.

Exceptions to the minimum charge amount apply to some payment methods, such as [iDEAL](https://docs.stripe.com/payments/ideal.md) (allows `amount` values as low as `1`).

In general, the number of allowed digits limits the maximum amount you can charge a customer. The `amount` value supports up to:

- 12 digits for IDR, for a maximum charge of 9,999,999,999.99 IDR (`999999999999`)
- 9 digits for IDR with American Express, for a maximum charge of 9,999,999.99 IDR (`999999999`)
- 9 digits for INR, for a maximum charge of 9,999,999.99 INR (`999999999`)
- 8 digits for all other currencies, for a maximum charge of 999,999.99 (`99999999`)

When accepting card payments, these currencies support higher maximum amounts:

- 11 digits for LBP, for a maximum charge of 999,999,999,999 LBP (`99999999999999`)
- 10 digits for COP, for a maximum charge of 9,999,999,999.9 COP (`9999999999999`)
- 10 digits for HUF, for a maximum charge of 9,999,999,999 HUF (`9999999999999`)
- 10 digits for JPY, for a maximum charge of 9,999,999,999 JPY (`9999999999999`)

Card networks can impose charge amount limits that are more restrictive than digit number.

> When processing JCB, Diners Club, and Discover cards from Japanese Stripe accounts, the maximum amount is 8 digits (99,999,999 JPY), regardless of the JPY currency limits listed above. Learn more about [accepting JCB payments in Japan](https://support.stripe.com/questions/enabling-jcb-payments-for-japan-based-stripe-accounts).

## European credit cards 

Some factors, like pricing, result in distinct treatment of credit cards from Europe compared to credit cards from other regions. Stripe defines European cards as cards issued in the following countries:

| Country code | Country                       |
| ------------ | ----------------------------- |
| AD           | Andorra                       |
| AT           | Austria                       |
| BE Belgium   |
| BG           | Bulgaria                      |
| HR           | Croatia                       |
| CY           | Cyprus                        |
| CZ           | Czech Republic                |
| DK           | Denmark                       |
| EE           | Estonia                       |
| FO           | Faroe Islands                 |
| FI           | Finland                       |
| FR           | France                        |
| DE           | Germany                       |
| GI           | Gibraltar                     |
| GR           | Greece                        |
| GL           | Greenland                     |
| GG           | Guernsey                      |
| VA           | Holy See (Vatican City State) |
| HU           | Hungary                       |
| IS           | Iceland                       |
| IE           | Ireland                       |
| IM           | Isle of Man                   |
| IT           | Italy                         |
| JE           | Jersey                        |
| LV           | Latvia                        |
| LI           | Liechtenstein                 |
| LT           | Lithuania                     |
| LU           | Luxembourg                    |
| MT           | Malta                         |
| MC           | Monaco                        |
| NL           | Netherlands                   |
| NO           | Norway                        |
| PL           | Poland                        |
| PT           | Portugal                      |
| RO           | Romania                       |
| PM           | Saint Pierre and Miquelon     |
| SM           | San Marino                    |
| SK           | Slovakia                      |
| SI           | Slovenia                      |
| ES           | Spain                         |
| SE           | Sweden                        |
| TR           | Türkiye                       |
| GB           | United Kingdom                |

## Countries with foreign exchange control 

Remittance to or from countries with foreign exchange control (including, but not limited to, Brazil) is carried out exclusively through authorized channels, pursuant to the legislation applicable in those countries.

## See also

- [Receive payouts](https://docs.stripe.com/payouts.md)
- [Localize prices](https://docs.stripe.com/payments/currencies/localize-prices.md)
