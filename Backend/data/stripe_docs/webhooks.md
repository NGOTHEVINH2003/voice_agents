# Receive Stripe events in your webhook endpoint

Listen for events in your Stripe account on your webhook endpoint so your integration can automatically trigger reactions.

> #### Send events to your AWS account
> 
> You can now send events directly to [Amazon EventBridge as an event destination](https://docs.stripe.com/event-destinations/eventbridge.md).

Create an event destination to receive events at an HTTPS webhook endpoint. After you register a webhook endpoint, Stripe can push real-time event data to your application’s webhook endpoint when [events](https://docs.stripe.com/event-destinations.md#events-overview) happen in your Stripe account. Stripe uses HTTPS to send webhook events to your app as a JSON payload that includes an [Event object](https://docs.stripe.com/api/events.md).

Receiving webhook events helps you respond to asynchronous events, such as when a customer’s bank confirms a payment, a customer disputes a charge, or a recurring payment succeeds.

## Get started 

To start receiving webhook events in your app:

1. Create a webhook endpoint handler to receive event data POST requests.
1. Test your webhook endpoint handler locally using the Stripe CLI.
1. Create a new [event destination](https://docs.stripe.com/event-destinations.md) for your webhook endpoint.
1. Secure your webhook endpoint.

You can register and create one endpoint to handle several different event types at the same time, or set up individual endpoints for specific events.

## Unsupported event type behaviors for organization event destinations

Stripe sends most event types asynchronously, but waits for a response for some event types. In these cases, Stripe behaves differently based on whether or not the event destination responds.

If your event destination receives [Organization](https://docs.stripe.com/get-started/account/orgs.md) events, those requiring a response have the following limitations:

- You can’t subscribe to `issuing_authorization.request` for organization destinations. Instead, set up a [webhook endpoint](https://docs.stripe.com/webhooks.md#example-endpoint) in a Stripe account within the organization to subscribe to this event type. Use `issuing_authorization.request` to authorize purchase requests in real-time.
- Organization destinations receiving `checkout_sessions.completed` can’t [handle redirect behavior](https://docs.stripe.com/checkout/fulfillment.md#redirect-hosted-checkout) when you embed [Checkout](https://docs.stripe.com/payments/checkout.md) directly in your website or redirect customers to a Stripe-hosted payment page. To influence Checkout redirect behavior, process this event type with a [webhook endpoint](https://docs.stripe.com/webhooks.md#example-endpoint) configured in a Stripe account within the organization.
- Organization destinations responding unsuccessfully to an `invoice.created` event can’t influence [automatic invoice finalization when using automatic collection](https://docs.stripe.com/billing/subscriptions/webhooks.md#understand). You must process this event type with a [webhook endpoint](https://docs.stripe.com/webhooks.md#example-endpoint) configured in a Stripe account within the organization to trigger automatic invoice finalization.

## Create a handler

Use the Stripe API reference to identify the [thin event objects](https://docs.stripe.com/api/v2/events/event-types.md) or [snapshot event objects](https://docs.stripe.com/api/events/object.md) your webhook handler needs to process.

Set up an HTTP or HTTPS endpoint function that can accept webhook requests with a POST method. If you’re still developing your endpoint function on your local machine, it can use HTTP. After it’s publicly accessible, your webhook endpoint function must use HTTPS.

Set up your endpoint function so that it:

- Handles POST requests with a JSON payload consisting of an [event object](https://docs.stripe.com/api/events/object.md).
- For [organization](https://docs.stripe.com/get-started/account/orgs.md) event handlers, it inspects the `context` value to determine which account in an organization generated the event, then sets the `Stripe-Context` header corresponding to the `context` value.
- Quickly returns a successful status code (`2xx`) prior to any complex logic that might cause a timeout. For example, you must return a `200` response before updating a customer’s invoice as paid in your accounting system.

> Use our [interactive webhook endpoint builder](https://docs.stripe.com/webhooks/quickstart.md) to build a webhook endpoint function in your programming language.

#### Example endpoint 

This code snippet is a webhook function configured to check for received events from a Stripe account, handle the events, and return a `200` responses. Reference the [snapshot](https://docs.stripe.com/event-destinations.md#events-overview) event handler when you use API v1 resources, and reference the [thin](https://docs.stripe.com/event-destinations.md#events-overview) event handler when you use API v2 resources.

#### Snapshot event handler

When you create a snapshot event handler, use the API object definition at the time of the event for your logic by accessing the event’s `data.object` fields. You can also retrieve the API resource from the Stripe API to access the latest and up-to-date object definition.

#### Ruby

```ruby
require 'json'

# Replace this endpoint secret with your unique endpoint secret key
# If you're testing with the CLI, run 'stripe listen' to find the secret key
# If you defined your endpoint using the API or the Dashboard, check your webhook settings for your endpoint secret: https://dashboard.stripe.com/webhooks
endpoint_secret = 'whsec_...';

# Using Sinatra
post '/webhook' do
  payload = request.body.read
  event = nil

  begin
    event = Stripe::Event.construct_from(
      JSON.parse(payload, symbolize_names: true)
    )
  rescue JSON::ParserError => e
    # Invalid payload
    status 400
    return
  end

  # Check that you have configured webhook signing
  if endpoint_secret
    # Retrieve the event by verifying the signature using the raw body and the endpoint secret
    signature = request.env['HTTP_STRIPE_SIGNATURE'];
    begin
      event = Stripe::Webhook.construct_event(
        payload, signature, endpoint_secret
      )
    rescue Stripe::SignatureVerificationError => e
      puts "⚠️  Webhook signature verification failed. #{e.message}"
      status 400
    end
  end

  # Handle the event
  case event.type
  when 'payment_intent.succeeded'
    payment_intent = event.data.object # contains a Stripe::PaymentIntent
    # Then define and call a method to handle the successful payment intent.
    # handle_payment_intent_succeeded(payment_intent)
  when 'payment_method.attached'
    payment_method = event.data.object # contains a Stripe::PaymentMethod
    # Then define and call a method to handle the successful attachment of a PaymentMethod.
    # handle_payment_method_attached(payment_method)
  # ... handle other event types
  else
    puts "Unhandled event type: #{event.type}"
  end

  status 200
end
```

#### Python

```python
import json
from django.http import HttpResponse

# Using Django
# Replace this endpoint secret with your unique endpoint secret key
# If you're testing with the CLI, run 'stripe listen' to find the secret key
# If you defined your endpoint using the API or the Dashboard, check your webhook settings for your endpoint secret: https://dashboard.stripe.com/webhooks
endpoint_secret = 'whsec_...'

@csrf_exempt
def my_webhook_view(request):
  payload = request.body
  event = None

  try:
    event = stripe.Event.construct_from(
      json.loads(payload), stripe.api_key
    )
  except ValueError as e:
    # Invalid payload
    return HttpResponse(status=400)

  if endpoint_secret:
        # Only verify the event if you've defined an endpoint secret
        # Otherwise, use the basic event deserialized with JSON
        sig_header = request.headers.get('stripe-signature')
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except stripe.error.SignatureVerificationError as e:
            print('⚠️  Webhook signature verification failed.' + str(e))
            return jsonify(success=False)

  # Handle the event
  if event.type == 'payment_intent.succeeded':
    payment_intent = event.data.object # contains a stripe.PaymentIntent
    # Then define and call a method to handle the successful payment intent.
    # handle_payment_intent_succeeded(payment_intent)
  elif event.type == 'payment_method.attached':
    payment_method = event.data.object # contains a stripe.PaymentMethod
    # Then define and call a method to handle the successful attachment of a PaymentMethod.
    # handle_payment_method_attached(payment_method)
  # ... handle other event types
  else:
    print('Unhandled event type {}'.format(event.type))

  return HttpResponse(status=200)
```

#### PHP

```php

// Replace this endpoint secret with your unique endpoint secret key
// If you're testing with the CLI, run 'stripe listen' to find the secret key
// # If you defined your endpoint using the API or the Dashboard, check your webhook settings for your endpoint secret: https://dashboard.stripe.com/webhooks
$endpoint_secret = 'whsec_...';

$payload = @file_get_contents('php://input');
$event = null;

try {
    $event = \Stripe\Event::constructFrom(
        json_decode($payload, true)
    );
} catch(\UnexpectedValueException $e) {
    // Invalid payload
    http_response_code(400);
    exit();
}

if ($endpoint_secret) {
  // Only verify the event if you've defined an endpoint secret
  // Otherwise, use the basic decoded event
  $sig_header = $_SERVER['HTTP_STRIPE_SIGNATURE'];
  try {
    $event = \Stripe\Webhook::constructEvent(
      $payload, $sig_header, $endpoint_secret
    );
  } catch(\Stripe\Exception\SignatureVerificationException $e) {
    // Invalid signature
    echo '⚠️  Webhook error while validating signature.';
    http_response_code(400);
    exit();
  }
}

// Handle the event
switch ($event->type) {
    case 'payment_intent.succeeded':
        $paymentIntent = $event->data->object; // contains a \Stripe\PaymentIntent
        // Then define and call a method to handle the successful payment intent.
        // handlePaymentIntentSucceeded($paymentIntent);
        break;
    case 'payment_method.attached':
        $paymentMethod = $event->data->object; // contains a \Stripe\PaymentMethod
        // Then define and call a method to handle the successful attachment of a PaymentMethod.
        // handlePaymentMethodAttached($paymentMethod);
        break;
    // ... handle other event types
    default:
        echo 'Received unknown event type ' . $event->type;
}

http_response_code(200);
```

#### Java

```java
// Using the Spark framework (http://sparkjava.com)
public Object handle(Request request, Response response) {
 // Replace this endpoint secret with your unique endpoint secret key
 // If you're testing with the CLI, run 'stripe listen' to find the secret key
 // I# If you defined your endpoint using the API or the Dashboard, check your webhook settings for your endpoint secret: https://dashboard.stripe.com/webhooks
  String endpointSecret = "whsec_...";

  String payload = request.body();
  Event event = null;

  try {
    event = ApiResource.GSON.fromJson(payload, Event.class);
  } catch (JsonSyntaxException e) {
    // Invalid payload
    response.status(400);
    return "";
  }
  String sigHeader = request.headers("Stripe-Signature");
  if(endpointSecret != null && sigHeader != null) {
      // Only verify the event if you’ve defined an endpoint secret
      // Otherwise, use the basic event deserialized with GSON
      try {
          event = Webhook.constructEvent(
              payload, sigHeader, endpointSecret
          );
      } catch (SignatureVerificationException e) {
          // Invalid signature
          System.out.println("⚠️  Webhook error while validating signature.");
          response.status(400);
          return "";
      }
  }
  // Deserialize the nested object inside the event
  EventDataObjectDeserializer dataObjectDeserializer = event.getDataObjectDeserializer();
  StripeObject stripeObject = null;
  if (dataObjectDeserializer.getObject().isPresent()) {
    stripeObject = dataObjectDeserializer.getObject().get();
  } else {
    // Deserialization failed, probably due to an API version mismatch.
    // Refer to the Javadoc documentation on `EventDataObjectDeserializer` for
    // instructions on how to handle this case, or return an error here.
  }

  // Handle the event
  switch (event.getType()) {
    case "payment_intent.succeeded":
      PaymentIntent paymentIntent = (PaymentIntent) stripeObject;
      // Then define and call a method to handle the successful payment intent.
      // handlePaymentIntentSucceeded(paymentIntent);
      break;
    case "payment_method.attached":
      PaymentMethod paymentMethod = (PaymentMethod) stripeObject;
      // Then define and call a method to handle the successful attachment of a PaymentMethod.
      // handlePaymentMethodAttached(paymentMethod);
      break;
    // ... handle other event types
    default:
      System.out.println("Unhandled event type: " + event.getType());
  }

  response.status(200);
  return "";
}
```

#### Node.js

```javascript
const express = require('express');
const app = express();

// Replace this endpoint secret with your unique endpoint secret key
// If you're testing with the CLI, run 'stripe listen' to find the secret key
// If you defined your endpoint using the API or the Dashboard, check your webhook settings for your endpoint secret: https://dashboard.stripe.com/webhooks
const endpointSecret = 'whsec_...';

// The express.raw middleware keeps the request body unparsed;
// this is necessary for the signature verification process
app.post('/webhook', express.raw({type: 'application/json'}), (request, response) => {
  let event;
  if (endpointSecret) {
    // Get the signature sent by Stripe
    const signature = request.headers['stripe-signature'];
    try {
      event = stripe.webhooks.constructEvent(
        request.body,
        signature,
        endpointSecret
      );
    } catch (err) {
      console.log(`⚠️ Webhook signature verification failed.`, err.message);
      return response.sendStatus(400);
    }

  // Handle the event
  switch (event.type) {
    case 'payment_intent.succeeded':
      const paymentIntent = event.data.object;
      // Then define and call a method to handle the successful payment intent.
      // handlePaymentIntentSucceeded(paymentIntent);
      break;
    case 'payment_method.attached':
      const paymentMethod = event.data.object;
      // Then define and call a method to handle the successful attachment of a PaymentMethod.
      // handlePaymentMethodAttached(paymentMethod);
      break;
    // ... handle other event types
    default:
      console.log(`Unhandled event type ${event.type}`);
  }

  // Return a response to acknowledge receipt of the event
  response.json({received: true});
});

app.listen(4242, () => console.log('Running on port 4242'));
```

#### Go

```go
http.HandleFunc("/webhook", func(w http.ResponseWriter, req *http.Request) {
    const MaxBodyBytes = int64(65536)
    req.Body = http.MaxBytesReader(w, req.Body, MaxBodyBytes)
    payload, err := ioutil.ReadAll(req.Body)
    if err != nil {
        fmt.Fprintf(os.Stderr, "Error reading request body: %v\n", err)
        w.WriteHeader(http.StatusServiceUnavailable)
        return
    }

    event := stripe.Event{}

    if err := json.Unmarshal(payload, &event); err != nil {
        fmt.Fprintf(os.Stderr, "Failed to parse webhook body json: %v\n", err.Error())
        w.WriteHeader(http.StatusBadRequest)
        return
    }

    // Unmarshal the event data into an appropriate struct depending on its Type
    switch event.Type {
    case "payment_intent.succeeded":
        var paymentIntent stripe.PaymentIntent
        err := json.Unmarshal(event.Data.Raw, &paymentIntent)
        if err != nil {
            fmt.Fprintf(os.Stderr, "Error parsing webhook JSON: %v\n", err)
            w.WriteHeader(http.StatusBadRequest)
            return
        }
        // Then define and call a func to handle the successful payment intent.
        // handlePaymentIntentSucceeded(paymentIntent)
    case "payment_method.attached":
        var paymentMethod stripe.PaymentMethod
        err := json.Unmarshal(event.Data.Raw, &paymentMethod)
        if err != nil {
            fmt.Fprintf(os.Stderr, "Error parsing webhook JSON: %v\n", err)
            w.WriteHeader(http.StatusBadRequest)
            return
        }
        // Then define and call a func to handle the successful attachment of a PaymentMethod.
        // handlePaymentMethodAttached(paymentMethod)
    // ... handle other event types
    default:
        fmt.Fprintf(os.Stderr, "Unhandled event type: %s\n", event.Type)
    }

    w.WriteHeader(http.StatusOK)
})
```

#### .NET

```csharp
using System;
using System.IO;
using Microsoft.AspNetCore.Mvc;
using Stripe;

namespace workspace.Controllers
{
    [Route("api/[controller]")]
    public class StripeWebHook : Controller
    {
        [HttpPost]
        public async Task<IActionResult> Index()
        {
            var json = await new StreamReader(HttpContext.Request.Body).ReadToEndAsync();
            const string endpointSecret = "whsec_...";
            try
            {
                var stripeEvent = EventUtility.ParseEvent(json);
                var signatureHeader = Request.Headers["Stripe-Signature"];

                stripeEvent = EventUtility.ConstructEvent(json,signatureHeader, endpointSecret);

                // Handle the event
                // If on SDK version < 46, use class Events instead of EventTypes
                if (stripeEvent.Type == EventTypes.PaymentIntentSucceeded)
                {
                    var paymentIntent = stripeEvent.Data.Object as PaymentIntent;
                    // Then define and call a method to handle the successful payment intent.
                    // handlePaymentIntentSucceeded(paymentIntent);
                }
                else if (stripeEvent.Type == EventTypes.PaymentMethodAttached)
                {
                    var paymentMethod = stripeEvent.Data.Object as PaymentMethod;
                    // Then define and call a method to handle the successful attachment of a PaymentMethod.
                    // handlePaymentMethodAttached(paymentMethod);
                }
                // ... handle other event types
                else
                {
                    // Unexpected event type
                    Console.WriteLine("Unhandled event type: {0}", stripeEvent.Type);
                }
                return Ok();
            }
            catch (StripeException e)
            {
                return BadRequest();
            }
        }
    }
}
```

#### Thin event handler (Clover+)

When you create a thin event handler, use the `fetchRelatedObject()` method to retrieve the latest version of the object associated with the event. Events might contain [additional data](https://docs.stripe.com/event-destinations.md#fetch-data) that you can only retrieve through the `.fetchEvent()` instance method on `EventNotification`. The exact shape of that data depends on the `type` of the Event.

Event types must be available at the time of release to generate classes in that SDK version. To handle Events the SDK doesn’t have classes for, use the `UnknownEventNotification` class.

#### Python

```python
import os
from stripe import StripeClient
from stripe.events import UnknownEventNotification

from flask import Flask, request, jsonify

app = Flask(__name__)
api_key = os.environ.get("STRIPE_API_KEY", "")
webhook_secret = os.environ.get("WEBHOOK_SECRET", "")

client = StripeClient(api_key)

@app.route("/webhook", methods=["POST"])
def webhook():
    webhook_body = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event_notif = client.parse_event_notification(
            webhook_body, sig_header, webhook_secret
        )

        # type checkers will narrow the type based on the `type` property
        if event_notif.type == "v1.billing.meter.error_report_triggered":
            # in this block, event_notification is typed as
            # a V1BillingMeterErrorReportTriggeredEventNotification

            # there's basic info about the related object in the notification
            print(f"Meter w/ id {event_notif.related_object.id} had a problem")

            # or you can fetch the full object form the API for more details
            meter = event_notif.fetch_related_object()
            print(
                f"Meter {meter.display_name} ({meter.id}) had a problem"
            )

            # And you can always fetch the full event:
            event = event_notif.fetch_event()
            print(f"More info: {event.data.developer_message_summary}")

        elif event_notif.type == "v1.billing.meter.no_meter_found":
            # in this block, event_notification is typed as
            # a V1BillingMeterNoMeterFoundEventNotification

            # that class doesn't define `fetch_related_object` because the event
            # has no related object.
            # so this line would correctly give a type error:
            # meter = event_notif.fetch_related_object()

            # but fetching the event always works:
            event = event_notif.fetch_event()
            print(
                f"Err! No meter found: {event.data.developer_message_summary}"
            )

        # Events that were introduced after this SDK version release are
        # represented as `UnknownEventNotification`s.
        # They're valid, the SDK just doesn't have corresponding classes for them.
        # You must match on the "type" property instead.
        elif isinstance(event_notif, UnknownEventNotification):
            # these lines are optional, but will give you more accurate typing in this block
            from typing import cast

            event_notif = cast(UnknownEventNotification, event_notif)

            # continue matching on the type property
            # from this point on, the `related_object` property _may_ be None
            # (depending on the event type)
            if event_notif.type == "some.new.event":
                # if this event type has a related object, you can fetch it
                obj = event_notif.fetch_related_object()
                # otherwise, `obj` will just be `None`
                print(f"Related object: {obj}")

                # you can still fetch the full event, but it will be untyped
                event = event_notif.fetch_event()
                print(f"New event: {event.data}")  # type: ignore

        return jsonify(success=True), 200
    except Exception as e:
        return jsonify(error=str(e)), 400
```

#### Ruby

```ruby
require "stripe"
require "sinatra"

api_key = ENV.fetch("STRIPE_API_KEY", nil)
# Retrieve the webhook secret from the environment variable
webhook_secret = ENV.fetch("WEBHOOK_SECRET", nil)

client = Stripe::StripeClient.new(api_key)

post "/webhook" do
  webhook_body = request.body.read
  sig_header = request.env["HTTP_STRIPE_SIGNATURE"]
  event_notification = client.parse_event_notification(webhook_body, sig_header, webhook_secret)

  if event_notification.instance_of?(Stripe::Events::V1BillingMeterErrorReportTriggeredEventNotification)
    # there's basic info about the related object in the notification
    puts "Received event for meter id:", event_notification.related_object.id

    # or you can fetch the full object form the API for more details
    meter = event_notification.fetch_related_object
    puts "Meter #{meter.display_name} (#{meter.id}) had a problem"

    # And you can always fetch the full event:
    event = event_notification.fetch_event
    puts "More info:", event.data.developer_message_summary
  elsif event_notification.instance_of?(Stripe::Events::UnknownEventNotification)
    # Events that were introduced after this SDK version release are
    # represented as `UnknownEventNotification`s.
    # They're valid, the SDK just doesn't have corresponding classes for them.
    # You must match on the "type" property instead.
    if event_notification.type == "some.new.event"
      # your logic goes here
    end
  end

  # Record the failures and alert your team
  status 200
end
```

#### PHP

```php
<?php

require 'vendor/autoload.php';

$api_key = getenv('STRIPE_API_KEY');
$webhook_secret = getenv('WEBHOOK_SECRET');

$app = new \Slim\App();
$client = new \Stripe\StripeClient($api_key);

$app->post('/webhook', static function ($request, $response) use ($client, $webhook_secret) {
    $webhook_body = $request->getBody()->getContents();
    $sig_header = $request->getHeaderLine('Stripe-Signature');

    try {
        $event_notification = $client->parseEventNotification($webhook_body, $sig_header, $webhook_secret);

        // check what type of event notification we have
        if ($event_notification instanceof Stripe\Events\V1BillingMeterErrorReportTriggeredEventNotification) {
            // there's basic info about the related object in the notification
            echo "Meter with id {$event_notification->related_object->id} reported an error\n";

            // or you can fetch the full object form the API for more details
            $meter = $event_notification->fetchRelatedObject();
            echo "Meter {$meter->display_name} ({$meter->id}) had a problem\n";

            # And you can always fetch the full event:
            $event = $event_notification->fetchEvent();
            echo "More info: {$event->data->developer_message_summary}\n";
        } else if ($event_notification instanceof Stripe\Events\UnknownEventNotification) {
            // Events that were introduced after this SDK version release are
            // represented as `UnknownEventNotification`s.
            // They're valid, the SDK just doesn't have corresponding classes for them.
            // You must match on the "type" property instead.
            if ($event_notification->type === 'some.new.event') {
                // handle it the same way as above
            }
        }

        return $response->withStatus(200);
    } catch (Exception $e) {
        return $response->withStatus(400)->withJson(['error' => $e->getMessage()]);
    }
});

$app->run();
```

#### Java

```java
import com.stripe.StripeClient;
import com.stripe.events.UnknownEventNotification;
import com.stripe.events.V1BillingMeterErrorReportTriggeredEvent;
import com.stripe.events.V1BillingMeterErrorReportTriggeredEventNotification;
import com.stripe.exception.StripeException;
import com.stripe.model.billing.Meter;
import com.stripe.model.v2.core.EventNotification;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;

public class EventNotificationWebhookHandler {
  private static final String API_KEY = System.getenv("STRIPE_API_KEY");
  private static final String WEBHOOK_SECRET = System.getenv("WEBHOOK_SECRET");

  private static final StripeClient client = new StripeClient(API_KEY);

  public static void main(String[] args) throws IOException {

    HttpServer server = HttpServer.create(new InetSocketAddress(4242), 0);
    server.createContext("/webhook", new WebhookHandler());
    server.setExecutor(null);
    server.start();
  }

  static class WebhookHandler implements HttpHandler {
    @Override
    public void handle(HttpExchange exchange) throws IOException {
      if ("POST".equals(exchange.getRequestMethod())) {
        InputStream requestBody = exchange.getRequestBody();
        String webhookBody = new String(requestBody.readAllBytes(), StandardCharsets.UTF_8);
        String sigHeader = exchange.getRequestHeaders().getFirst("Stripe-Signature");

        try {
          EventNotification notif =
              client.parseEventNotification(webhookBody, sigHeader, WEBHOOK_SECRET);

          if (notif instanceof V1BillingMeterErrorReportTriggeredEventNotification) {
            V1BillingMeterErrorReportTriggeredEventNotification eventNotification =
                (V1BillingMeterErrorReportTriggeredEventNotification) notif;

            // there's basic info about the related object in the notification
            System.out.println(
                "Meter w/ id " + eventNotification.getRelatedObject().getId() + " had a problem");

            // or you can fetch the full object form the API for more details
            Meter meter = eventNotification.fetchRelatedObject();
            StringBuilder sb = new StringBuilder();
            sb.append("Meter ")
                .append(meter.getDisplayName())
                .append(" (")
                .append(meter.getId())
                .append(") had a problem");
            System.out.println(sb.toString());

            // And you can always fetch the full event:
            V1BillingMeterErrorReportTriggeredEvent event = eventNotification.fetchEvent();
            System.out.println("More info: " + event.getData().getDeveloperMessageSummary());
          } else if (notif instanceof UnknownEventNotification) {
            // Events that were introduced after this SDK version release are
            // represented as `UnknownEventNotification`s.
            // They're valid, the SDK just doesn't have corresponding classes for them.
            // You must match on the "type" property instead.
            UnknownEventNotification unknownEvent = (UnknownEventNotification) notif;
            if (unknownEvent.getType().equals("some.new.event")) {
              // you can still `.fetchEvent()` and `.fetchRelatedObject()`, but the latter may
              // return `null` if that event type doesn't have a related object.
            }
          }

          exchange.sendResponseHeaders(200, -1);
        } catch (StripeException e) {
          exchange.sendResponseHeaders(400, -1);
        }
      } else {
        exchange.sendResponseHeaders(405, -1);
      }
      exchange.close();
    }
  }
}
```

#### Typescript

```typescript
import {Stripe} from 'stripe';
import express from 'express';

const app = express();

const apiKey = process.env.STRIPE_API_KEY ?? '';
const webhookSecret = process.env.WEBHOOK_SECRET ?? '';

const client = new Stripe(apiKey);

app.post(
  '/webhook',
  express.raw({type: 'application/json'}),
  async (req, res) => {
    const sig = req.headers['stripe-signature'] ?? '';

    try {
      const eventNotification = client.parseEventNotification(
        req.body,
        sig,
        webhookSecret
      );

      // TS will narrow event based on the `type` property
      if (eventNotification.type == 'v1.billing.meter.error_report_triggered') {
        // this this block, eventNotification is correctly
        // a Stripe.Events.V1BillingMeterErrorReportTriggeredEventNotification

        // there's basic info about the related object in the notification
        console.log(
          `Meter w/ id ${eventNotification.related_object.id} had a problem`
        );

        // or you can fetch the full object from the API for more details
        const meter = await eventNotification.fetchRelatedObject();
        console.log(`Meter ${meter.display_name} (${meter.id}) had a problem`);

        // And you can always fetch the full event:
        const event = await eventNotification.fetchEvent();
        console.log(`More info: ${event.data.developer_message_summary}`);
      } else if (eventNotification.type === 'v1.billing.meter.no_meter_found') {
        // in this block, eventNotification is correctly
        // a Stripe.Events.V1BillingMeterNoMeterFoundEventNotification

        // that interface doesn't define `fetchRelatedObject()` because the event
        // has no related object. so this line would correctly give a type error:
        // eventNotification.fetchRelatedObject();

        // but fetching the event always works:
        const event = await eventNotification.fetchEvent();
        console.log(
          `Err: No meter found: ${event.data.developer_message_summary}`
        );
      // Events that were introduced after this SDK version release are
      // represented as `UnknownEventNotification`s.
      // They're valid, the SDK just doesn't have corresponding classes for them.
      // In that case, you ignore the type mismatch and cast to UnknownEventNotification
      // @ts-expect-error
      } else if (eventNotification.type === 'some.new.event') {
        const unknownEvent = eventNotification as Stripe.Events.UnknownEventNotification;

        // you can still fetch the related object, if one exists
        // but its type is `unknown`
        const obj = await unknownEvent.fetchRelatedObject();

        // and you can still fetch the event:
        const event = await unknownEvent.fetchEvent();
        // @ts-expect-error
        console.log(`Got new event: ${event.data}`);
      }

      res.sendStatus(200);
    } catch (err) {
      console.log(`Webhook Error: ${(err as any).stack}`);
      res.status(400).send(`Webhook Error: ${(err as any).message}`);
    }
  }
);

app.listen(4242, () => console.log('Running on port 4242'));
```

#### Go

```go
package main

import (
  "context"
  "io"
  "log/slog"
  "net/http"
  "os"

  "github.com/stripe/stripe-go/v83"
)

func main() {
	http.HandleFunc("/webhook", func(w http.ResponseWriter, req *http.Request) {
		const MaxBodyBytes = int64(65536)
		req.Body = http.MaxBytesReader(w, req.Body, MaxBodyBytes)
		payload, err := io.ReadAll(req.Body)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error reading request body: %v\n", err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}

		eventNotification, err := client.ParseEventNotification(payload, req.Header.Get("Stripe-Signature"), webhookSecret)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error reading request body: %v\n", err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}

		// Unmarshal the event data into an appropriate struct depending on its Type
		switch evt := eventNotification.(type) {
		case *stripe.V1BillingMeterErrorReportTriggeredEventNotification:
			// there's basic info about the related object in the notification
			fmt.Printf("Meter w/ id %s had a problem\n", evt.RelatedObject.ID)

			// or you can fetch the full object form the API for more details
			meter, err := evt.FetchRelatedObject(context.TODO())
			if err != nil {
				fmt.Fprintf(os.Stderr, "Error fetching related object: %v\n", err)
				w.WriteHeader(http.StatusInternalServerError)
				return
			}
			sb := fmt.Sprintf("Meter %s (%s) had a problem", meter.DisplayName, meter.ID)
			fmt.Println(sb)

			// And you can always fetch the full event:
			event, err := evt.FetchEvent(context.TODO())
			if err != nil {
				fmt.Fprintf(os.Stderr, "Error fetching event: %v\n", err)
				w.WriteHeader(http.StatusInternalServerError)
				return
			}
			fmt.Printf("More info: %s\n", event.Data.DeveloperMessageSummary)
		case *stripe.UnknownEventNotification:
			// Events that were introduced after this SDK version release are
      // represented as `UnknownEventNotification`s.
      // They're valid, the SDK just doesn't have corresponding classes for them.
      // You must match on the "type" property instead.
			switch evt.Type {
			case "some.new.event":
				// you can still `.FetchEvent()` and `.FetchRelatedObject()`, but the latter may
				// return `nil` if that event type doesn't have a related object.
				return
			}

		default:
			fmt.Fprintf(os.Stderr, "Purposefully skipping the handling of event w/ type: %s\n", evt.GetEventNotification().Type)
		}

		w.WriteHeader(http.StatusOK)
	})

	err := http.ListenAndServe(":4242", nil)
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
```

#### .NET

```csharp
using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Stripe;
using Stripe.Events;
[Route("api/[controller]")]
[ApiController]
public class EventNotificationWebhookHandler : ControllerBase
{
    private readonly StripeClient client;
    private readonly string webhookSecret;

    public EventNotificationWebhookHandler()
    {
        var apiKey = Environment.GetEnvironmentVariable("STRIPE_API_KEY");
        client = new StripeClient(apiKey);

        webhookSecret = Environment.GetEnvironmentVariable("WEBHOOK_SECRET") ?? string.Empty;
    }

    [HttpPost]
    public async Task<IActionResult> Index()
    {
        var json = await new StreamReader(HttpContext.Request.Body).ReadToEndAsync();
        try
        {
            var eventNotification = client.ParseEventNotification(json, Request.Headers["Stripe-Signature"], webhookSecret);

            // match on the type of the class to determine what event you have
            if (eventNotification is V1BillingMeterErrorReportTriggeredEventNotification notif)
            {
                // there's basic info about the related object in the notification
                Console.WriteLine(
                    $"Meter w/ id {notif.RelatedObject.Id} had a problem");

                // or you can fetch the full object form the API for more details
                var meter = await notif.FetchRelatedObjectAsync();
                Console.WriteLine($"Meter {meter.DisplayName} ({meter.Id}) had a problem");

                // And you can always fetch the full event:
                var evt = await notif.FetchEventAsync();
                Console.WriteLine($"More info: {evt.Data.DeveloperMessageSummary}");
            }
            else if (eventNotification is UnknownEventNotification unknownEvt)
            {
                // Events that were introduced after this SDK version release are
                // represented as `UnknownEventNotification`s.
                // They're valid, the SDK just doesn't have corresponding classes for them.
                // You must match on the "type" property instead.
                if (unknownEvt.Type == "some.other.event")
                {
                    // you can still `.fetchEvent()` and `.fetchRelatedObject()`, but the latter may
                    // return `null` if that event type doesn't have a related object.
                }
            }

            return Ok();
        }
        catch (StripeException e)
        {
            return BadRequest(e.Message);
        }
    }
}
```

#### Thin event handler (Acacia or Basil)

When you create a thin event handler, use the `fetchRelatedObject()` method to retrieve the latest version of the object associated with the event. Thin events might contain [additional contextual data](https://docs.stripe.com/event-destinations.md#fetch-data) that you can only retrieve with the API. Use the `retrieve()` call with the thin event ID to access these additional payload fields.

#### Python

```python
import os
from stripe import StripeClient
from stripe.events import V1BillingMeterErrorReportTriggeredEvent

from flask import Flask, request, jsonify

app = Flask(__name__)
api_key = os.environ.get('STRIPE_API_KEY')
webhook_secret = os.environ.get('WEBHOOK_SECRET')

client = StripeClient(api_key)

@app.route('/webhook', methods=['POST'])
def webhook():
    webhook_body = request.data
    sig_header = request.headers.get('Stripe-Signature')

try:
    thin_event = client.parse_thin_event(webhook_body, sig_header, webhook_secret)

    # Fetch the event data to understand the failure
    event = client.v2.core.events.retrieve(thin_event.id)
    if isinstance(event, V1BillingMeterErrorReportTriggeredEvent):
        meter = event.fetch_related_object()
        meter_id = meter.id

        # Record the failures and alert your team
        # Add your logic here

    return jsonify(success=True), 200
except Exception as e:
    return jsonify(error=str(e)), 400

if __name__ == '__main__':
    app.run(port=4242)
```

#### Ruby

```ruby
require "stripe"
require "sinatra"

api_key = ENV.fetch("STRIPE_API_KEY", nil)
# Retrieve the webhook secret from the environment variable
webhook_secret = ENV.fetch("WEBHOOK_SECRET", nil)

client = Stripe::StripeClient.new(api_key)

post "/webhook" do
  webhook_body = request.body.read
  sig_header = request.env["HTTP_STRIPE_SIGNATURE"]
  thin_event = client.parse_thin_event(webhook_body, sig_header, webhook_secret)

  # Fetch the event data to understand the failure
  event = client.v2.core.events.retrieve(thin_event.id)
  if event.instance_of? Stripe::V1BillingMeterErrorReportTriggeredEvent
    meter = event.fetch_related_object
    meter_id = meter.id
  end

  # Record the failures and alert your team
  # Add your logic here
  status 200
end
```

#### PHP

```php
<?php

require 'vendor/autoload.php';

$api_key = getenv('STRIPE_API_KEY');
$webhook_secret = getenv('WEBHOOK_SECRET');

$app = new \Slim\App();
$client = new \Stripe\StripeClient($api_key);

$app->post('/webhook', function ($request, $response) use ($client, $webhook_secret) {
    $webhook_body = $request->getBody()->getContents();
    $sig_header = $request->getHeaderLine('Stripe-Signature');

    try {
        $thin_event = $client->parseThinEvent($webhook_body, $sig_header, $webhook_secret);

        // Fetch the event data to understand the failure
        $event = $client->v2->core->events->retrieve($thin_event->id);
        if ($event instanceof \Stripe\Events\V1BillingMeterErrorReportTriggeredEvent) {
            $meter = $event->fetchRelatedObject();
            $meter_id = $meter->id;

            // Record the failures and alert your team
            // Add your logic here
        }
        return $response->withStatus(200);
    } catch (\Exception $e) {
        return $response->withStatus(400)->withJson(['error' => $e->getMessage()]);
    }
});

$app->run();
```

#### Java

```java
import com.stripe.StripeClient;
import com.stripe.events.V1BillingMeterErrorReportTriggeredEvent;
import com.stripe.exception.StripeException;
import com.stripe.model.ThinEvent;
import com.stripe.model.billing.Meter;
import com.stripe.model.v2.Event;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.io.InputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;

public class StripeWebhookHandler {
  private static final String API_KEY = System.getenv("STRIPE_API_KEY");
  private static final String WEBHOOK_SECRET = System.getenv("WEBHOOK_SECRET");

  private static final StripeClient client = new StripeClient(API_KEY);

  public static void main(String[] args) throws IOException {

    HttpServer server = HttpServer.create(new InetSocketAddress(4242), 0);
    server.createContext("/webhook", new WebhookHandler());
    server.setExecutor(null);
    server.start();
  }

  static class WebhookHandler implements HttpHandler {
    @Override
    public void handle(HttpExchange exchange) throws IOException {
      if ("POST".equals(exchange.getRequestMethod())) {
        InputStream requestBody = exchange.getRequestBody();
        String webhookBody = new String(requestBody.readAllBytes(), StandardCharsets.UTF_8);
        String sigHeader = exchange.getRequestHeaders().getFirst("Stripe-Signature");

        try {
          ThinEvent thinEvent = client.parseThinEvent(webhookBody, sigHeader, WEBHOOK_SECRET);

          // Fetch the event data to understand the failure
          Event baseEvent = client.v2().core().events().retrieve(thinEvent.getId());
          if (baseEvent instanceof V1BillingMeterErrorReportTriggeredEvent) {
            V1BillingMeterErrorReportTriggeredEvent event =
                (V1BillingMeterErrorReportTriggeredEvent) baseEvent;
            Meter meter = event.fetchRelatedObject();

            String meterId = meter.getId();

            // Record the failures and alert your team
            // Add your logic here
          }

          exchange.sendResponseHeaders(200, -1);
        } catch (StripeException e) {
          exchange.sendResponseHeaders(400, -1);
        }
      } else {
        exchange.sendResponseHeaders(405, -1);
      }
      exchange.close();
    }
  }
}
```

#### Node.js

```javascript
const express = require('express');
const {Stripe} = require('stripe');

const app = express();

const apiKey = process.env.STRIPE_API_KEY;
const webhookSecret = process.env.WEBHOOK_SECRET;

const client = new Stripe(apiKey);

app.post(
  '/webhook',
  express.raw({type: 'application/json'}),
  async (req, res) => {
    const sig = req.headers['stripe-signature'];

    try {
      const thinEvent = client.parseThinEvent(req.body, sig, webhookSecret);

      // Fetch the event data to understand the failure
      const event = await client.v2.core.events.retrieve(thinEvent.id);
      if (event.type == 'v1.billing.meter.error_report_triggered') {
        const meter = await event.fetchRelatedObject();
        const meterId = meter.id;
        // Record the failures and alert your team
        // Add your logic here
      }
      res.sendStatus(200);
    } catch (err) {
      console.log(`Webhook Error: ${err.message}`);
      res.status(400).send(`Webhook Error: ${err.message}`);
    }
  },
);

app.listen(4242, () => console.log('Running on port 4242'));
```

#### Go

```go
package main

import (
  "context"
  "io"
  "log/slog"
  "net/http"
  "os"

  "github.com/stripe/stripe-go/v82"
)

func main() {
  apiKey := os.Getenv("STRIPE_API_KEY")
  webhookSecret := os.Getenv("STRIPE_WEBHOOK_SECRET")
  client := stripe.NewClient(apiKey)

  http.HandleFunc("/webhook", func(w http.ResponseWriter, req *http.Request) {
    defer req.Body.Close()
    payload, err := io.ReadAll(req.Body)
    if err != nil {
      slog.Error("Reading request body", "error", err)
      w.WriteHeader(http.StatusInternalServerError)
      return
    }
    thinEvent, err := client.ParseThinEvent(payload, req.Header.Get("Stripe-Signature"), webhookSecret)
    if err != nil {
      slog.Error("Parsing thin event", "error", err)
      w.WriteHeader(http.StatusInternalServerError)
      return
    }
    event, err := client.V2CoreEvents.Retrieve(context.TODO(), thinEvent.ID, nil)
    if err != nil {
      slog.Error("Retrieving snapshot event", "error", err)
      w.WriteHeader(http.StatusInternalServerError)
      return
    }

    switch e := event.(type) {
    case *stripe.V1BillingMeterErrorReportTriggeredEvent:
      meter, err := e.FetchRelatedObject()
      if err != nil {
        slog.Error("Error fetching related object", "error", err)
        w.WriteHeader(http.StatusInternalServerError)
        return
      }
      meterID := meter.ID
      // Add your logic here
    }

    w.WriteHeader(http.StatusOK)
  })
  err := http.ListenAndServe(":4242", nil)
  if err != nil {
    slog.Error("Starting server", "error", err)
    os.Exit(1)
  }
}
```

#### .NET

```csharp
using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Stripe;
using Stripe.Events;
[Route("api/[controller]")]
[ApiController]
public class WebhookController : ControllerBase
{
    private readonly StripeClient _client;
    private readonly string _webhookSecret;
    public WebhookController()
    {
        var apiKey = Environment.GetEnvironmentVariable("STRIPE_API_KEY");
        _client = new StripeClient(apiKey);
        _webhookSecret = Environment.GetEnvironmentVariable("WEBHOOK_SECRET");
    }
    [HttpPost]
    public async Task<IActionResult> Index()
    {
        var json = await new StreamReader(HttpContext.Request.Body).ReadToEndAsync();
        try
        {
            var thinEvent = _client.ParseThinEvent(json, Request.Headers["Stripe-Signature"], _webhookSecret);
            // Fetch the event data to understand the failure
            var baseEvent = await _client.V2.Core.Events.GetAsync(thinEvent.Id);
            if (baseEvent is V1BillingMeterErrorReportTriggeredEvent fullEvent)
            {
                var meter = await fullEvent.FetchRelatedObjectAsync();
                var meterId = meter.Id;
                // Record the failures and alert your team
                // Add your logic here
            }
            return Ok();
        }
        catch (StripeException e)
        {
            return BadRequest(e.Message);
        }
    }
}
```

#### Using `context` 

#### Snapshot events

This code snippet is a webhook function configured to check for received events, detect the originating account if applicable, handle the event, and return a `200` response.

#### Ruby

```ruby
require 'json'

# Using Sinatra
post '/webhook' do
  payload = request.body.read
  event = nil

  begin
    event = Stripe::Event.construct_from(
      JSON.parse(payload, symbolize_names: true)
    )
  rescue JSON::ParserError => e
    # Invalid payload
    status 400
    return
  end

  # Extract the context
  context = event.context

  # Define your API key variables (ideally loaded securely)
  ACCOUNT_123_API_KEY = "sk_test_123"
  ACCOUNT_456_API_KEY = "sk_test_456"

  account_api_keys = {
    "account_123" => ACCOUNT_123_API_KEY,
    "account_456" => ACCOUNT_456_API_KEY
  }

  api_key = account_api_keys[context]

  if api_key.nil?
    puts "No API key found for context: #{context}"
    status 400
    return
  end

  # Handle the event
  case event.type
  when 'customer.created'
    customer = event.data.object

    begin
      latest_customer = Stripe::Customer.retrieve(
        customer.id,
        { api_key: api_key }
      )
      handle_customer_created(latest_customer, context)
    rescue => e
      puts "Error retrieving customer: #{e.message}"
      status 500
      return
    end

  when 'payment_method.attached'
    payment_method = event.data.object

    begin
      latest_payment_method = Stripe::PaymentMethod.retrieve(
        payment_method.id,
        { api_key: api_key }
      )
      handle_payment_method_attached(latest_payment_method, context)
    rescue => e
      puts "Error retrieving payment method: #{e.message}"
      status 500
      return
    end

  else
    puts "Unhandled event type: #{event.type}"
  end

  status 200
end
```

#### Python

```python
import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

# Define API key variables (in production, pull these from environment variables or secret manager)
ACCOUNT_123_API_KEY = "sk_test_123"
ACCOUNT_456_API_KEY = "sk_test_456"

account_api_keys = {
    "account_123": ACCOUNT_123_API_KEY,
    "account_456": ACCOUNT_456_API_KEY,
}

@csrf_exempt
def my_webhook_view(request):
    payload = request.body
    event = None

    try:
        event = stripe.Event.construct_from(
            json.loads(payload.decode('utf-8')), stripe.api_key
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)

    # Extract context
    context = getattr(event, "context", None)
    if context is None:
        print("Missing context in event.")
        return HttpResponse(status=400)

    api_key = account_api_keys.get(context)
    if api_key is None:
        print(f"No API key found for context: {context}")
        return HttpResponse(status=400)

    # Handle the event
    if event.type == 'customer.created':
        customer = event.data.object
        try:
            latest_customer = stripe.Customer.retrieve(customer.id, api_key=api_key)
            handle_customer_created(latest_customer, context)
        except Exception as e:
            print(f"Error retrieving customer: {e}")
            return HttpResponse(status=500)

    elif event.type == 'payment_method.attached':
        payment_method = event.data.object
        try:
            latest_payment_method = stripe.PaymentMethod.retrieve(payment_method.id, api_key=api_key)
            handle_payment_method_attached(latest_payment_method, context)
        except Exception as e:
            print(f"Error retrieving payment method: {e}")
            return HttpResponse(status=500)

    else:
        print(f'Unhandled event type {event.type}')

    return HttpResponse(status=200)
```

#### Java

```java
// Using the Spark framework
public Object handle(Request request, Response response) {
  String payload = request.body();
  Event event = null;

  try {
    event = ApiResource.GSON.fromJson(payload, Event.class);
  } catch (JsonSyntaxException e) {
    // Invalid payload
    response.status(400);
    return "";
  }

  // Get context from event
  String context = event.getContext();
  if (context == null || context.isEmpty()) {
    System.out.println("Missing context in event.");
    response.status(400);
    return "";
  }

  // Define your API key variables (in production, pull from environment or secrets manager)
  final String ACCOUNT_123_API_KEY = "sk_test_123";
  final String ACCOUNT_456_API_KEY = "sk_test_456";

  Map<String, String> accountApiKeys = new HashMap<>();
  accountApiKeys.put("account_123", ACCOUNT_123_API_KEY);
  accountApiKeys.put("account_456", ACCOUNT_456_API_KEY);

  String apiKey = accountApiKeys.get(context);
  if (apiKey == null) {
    System.out.println("No API key found for context: " + context);
    response.status(400);
    return "";
  }

  // Deserialize the nested object inside the event
  EventDataObjectDeserializer dataObjectDeserializer = event.getDataObjectDeserializer();
  if (!dataObjectDeserializer.getObject().isPresent()) {
    System.out.println("Unable to deserialize object from event.");
    response.status(400);
    return "";
  }

  StripeObject stripeObject = dataObjectDeserializer.getObject().get();

  // Set up RequestOptions with the correct API key
  RequestOptions requestOptions = RequestOptions.builder()
    .setApiKey(apiKey)
    .build();

  try {
    switch (event.getType()) {
      case "customer.created":
        Customer customerEvent = (Customer) stripeObject;
        // Fetch the latest Customer from Stripe using the account's API key
        Customer latestCustomer = Customer.retrieve(customerEvent.getId(), requestOptions);
        handleCustomerCreated(latestCustomer, context);
        break;

      case "payment_method.attached":
        PaymentMethod paymentMethodEvent = (PaymentMethod) stripeObject;
        // Fetch the latest PaymentMethod from Stripe using the account's API key
        PaymentMethod latestPaymentMethod = PaymentMethod.retrieve(paymentMethodEvent.getId(), requestOptions);
        handlePaymentMethodAttached(latestPaymentMethod, context);
        break;

      // ... handle other event types

      default:
        System.out.println("Unhandled event type: " + event.getType());
    }
  } catch (StripeException e) {
    System.out.println("Stripe API error: " + e.getMessage());
    response.status(500);
    return "";
  }

  response.status(200);
  return "";
}
```

#### Node.js

```javascript
// This example uses Express to receive webhooks
const express = require('express');
const app = express();

app.use(express.json({ type: 'application/json' }));

// Define your API key variables (in production, load from environment variables or secrets)
const ACCOUNT_123_API_KEY = 'sk_test_123';
const ACCOUNT_456_API_KEY = 'sk_test_456';

const accountApiKeys = {
  account_123: ACCOUNT_123_API_KEY,
  account_456: ACCOUNT_456_API_KEY,
};

app.post('/webhook', async (request, response) => {
  const event = request.body;

  const context = event.context;
  if (!context) {
    console.error('Missing context in event');
    return response.status(400).send('Missing context');
  }

  const apiKey = accountApiKeys[context];
  if (!apiKey) {
    console.error(`No API key found for context: ${context}`);
    return response.status(400).send('Unknown context');
  }

  const stripe = Stripe(apiKey);

  try {
    switch (event.type) {
      case 'customer.created': {
        const customer = event.data.object;
        const latestCustomer = await stripe.customers.retrieve(customer.id);
        handleCustomerCreated(latestCustomer, context);
        break;
      }
      case 'payment_method.attached': {
        const paymentMethod = event.data.object;
        const latestPaymentMethod = await stripe.paymentMethods.retrieve(paymentMethod.id);
        handlePaymentMethodAttached(latestPaymentMethod, context);
        break;
      }
      // ... handle other event types
      default:
        console.log(`Unhandled event type ${event.type}`);
    }

    response.json({ received: true });
  } catch (err) {
    console.error(`Error processing event: ${err.message}`);
    response.status(500).send('Internal error');
  }
});

app.listen(4242, () => console.log('Running on port 4242'));
```

#### .NET

```dotnet
using System;
using System.IO;
using Microsoft.AspNetCore.Mvc;
using Stripe;

namespace workspace.Controllers
{
    [Route("api/[controller]")]
    public class StripeWebHook : Controller
    {
        // Define your API key variables (these should ideally come from secure config or env vars)
        private const string ACCOUNT_123_API_KEY = "sk_test_123";
        private const string ACCOUNT_456_API_KEY = "sk_test_456";

        private readonly Dictionary<string, string> accountApiKeys = new()
        {
            { "account_123", ACCOUNT_123_API_KEY },
            { "account_456", ACCOUNT_456_API_KEY }
        };

        [HttpPost]
        public async Task<IActionResult> Index()
        {
            var json = await new StreamReader(HttpContext.Request.Body).ReadToEndAsync();

            try
            {
                var stripeEvent = EventUtility.ParseEvent(json);
                var context = stripeEvent.Context;

                if (string.IsNullOrEmpty(context))
                {
                    Console.WriteLine("Missing context in event");
                    return BadRequest();
                }

                if (!accountApiKeys.TryGetValue(context, out var apiKey))
                {
                    Console.WriteLine($"No API key found for context: {context}");
                    return BadRequest();
                }

                var requestOptions = new RequestOptions
                {
                    ApiKey = apiKey
                };

                // Handle the event
                if (stripeEvent.Type == Events.CustomerCreated)
                {
                    var customerEvent = stripeEvent.Data.Object as Customer;
                    if (customerEvent != null)
                    {
                        var customerService = new CustomerService();
                        var latestCustomer = await customerService.GetAsync(customerEvent.Id, null, requestOptions);
                        HandleCustomerCreated(latestCustomer, context);
                    }
                }
                else if (stripeEvent.Type == Events.PaymentMethodAttached)
                {
                    var paymentMethodEvent = stripeEvent.Data.Object as PaymentMethod;
                    if (paymentMethodEvent != null)
                    {
                        var paymentMethodService = new PaymentMethodService();
                        var latestPaymentMethod = await paymentMethodService.GetAsync(paymentMethodEvent.Id, null, requestOptions);
                        HandlePaymentMethodAttached(latestPaymentMethod, context);
                    }
                }
                else
                {
                    Console.WriteLine("Unhandled event type: {0}", stripeEvent.Type);
                }

                return Ok();
            }
            catch (StripeException e)
            {
                Console.WriteLine($"Stripe error: {e.Message}");
                return BadRequest();
            }
        }

        private void HandleCustomerCreated(Customer customer, string context)
        {
            Console.WriteLine($"Handled customer {customer.Id} for context {context}");
            // Your custom logic here
        }

        private void HandlePaymentMethodAttached(PaymentMethod paymentMethod, string context)
        {
            Console.WriteLine($"Handled payment method {paymentMethod.Id} for context {context}");
            // Your custom logic here
        }
    }
}
```

#### Thin event handler (Clover+)

Use the `EventNotification`’s `context` property to identify the account for events within your [organization](https://docs.stripe.com/get-started/account/orgs.md). You must set the [Stripe-Context header](https://docs.stripe.com/context.md) manually for all API calls except `.fetchRelatedObject()` and `.fetchEvent()`, which do this for you automatically.

#### Python

```python
org_api_key = os.environ.get("STRIPE_API_KEY")
webhook_secret = os.environ.get("WEBHOOK_SECRET")
client = StripeClient(org_api_key)

# inside your webhook handler
event_notification = client.parse_event_notification(payload, sig_header, webhook_secret)

# uses `context` automatically
event_notification.fetch_event()

# pass context manually for other API requests
client.v1.invoices.list(stripe_context=event_notification.context)
```

#### Ruby

```ruby
api_key = ENV.fetch("STRIPE_API_KEY", nil)
webhook_secret = ENV.fetch("WEBHOOK_SECRET", nil)
client = Stripe::StripeClient.new(api_key)

# inside your webhook handler
event_notification = client.parse_event_notification(payload, sig_header, webhook_secret)

# uses `context` automatically
event_notification.fetch_event

# pass context manually for other API requests
client.v1.invoices.list(nil, { stripe_context: event_notification.context })
```

#### Typescript

```typescript
const orgApiKey = process.env.STRIPE_API_KEY;
const webhookSecret = process.env.WEBHOOK_SECRET;
const client = new Stripe(orgApiKey);

// inside your webhook handler
const eventNotification = client.parseEventNotification(
  req.body,
  sig,
  webhookSecret
);

// uses `context` automatically:
await eventNotification.fetchEvent()

// pass context manually for other reuqests:
client.invoices.list(undefined, {
  stripeContext: eventNotification.context,
});
```

#### Java

```java
String orgApiKey = System.getenv("STRIPE_API_KEY");
String webhookSecret = System.getenv("WEBHOOK_SECRET");
StripeClient client = new StripeClient(orgApiKey);

// inside your webhook handler
EventNotification notif =
              client.parseEventNotification(webhookBody, sigHeader, WEBHOOK_SECRET);

// cast to a more specific type
V1BillingMeterErrorReportTriggeredEventNotification eventNotification =
      (V1BillingMeterErrorReportTriggeredEventNotification) notif;

// uses `context` automatically
eventNotification.fetchEvent();

// pass context manually for other API requests
client
    .v1()
    .invoices()
    .list(
        new RequestOptions.RequestOptionsBuilder()
            .setStripeContext(eventNotification.context)
            .build());
```

#### PHP

```php
$org_api_key = getenv('STRIPE_API_KEY');
$webhook_secret = getenv('WEBHOOK_SECRET');
$client = new \Stripe\StripeClient($org_api_key);

// inside your webhook handler
$event_notification = $client->parseEventNotification($webhook_body, $sig_header, $webhook_secret);

// uses context automatically
$event_notification->fetchEvent();

// pass context manually for other API requests
$client->invoices->all(null, ["stripe_context" => $event_notification->context]);
```

#### Go

```go
orgApiKey := os.Getenv("STRIPE_API_KEY")
webhookSecret := os.Getenv("WEBHOOK_SECRET")
client := stripe.NewClient(orgApiKey)

// inside your webhook handler
eventNotification, err := client.ParseEventNotification(payload, req.Header.Get("Stripe-Signature"), webhookSecret)
if err != nil {
  fmt.Fprintf(os.Stderr, "Error reading request body: %v\n", err)
  w.WriteHeader(http.StatusInternalServerError)
  return
}

// cast to a more specific type
switch evt := eventNotification.(type) {
case *stripe.V1BillingMeterErrorReportTriggeredEventNotification:
  // sets `Stripe-Context` automatically
  evt.FetchEvent(context.TODO())


  // pass context manually for other API requests
  client.V1Invoices.Retrieve(context.TODO(), "inv_123", &stripe.InvoiceRetrieveParams{
    Params: stripe.Params{
      StripeContext: evt.Context.StringPtr(),
    },
  })
}
```

#### .NET

```csharp
_client = new StripeClient(Environment.GetEnvironmentVariable("STRIPE_API_KEY"));
_webhookSecret = Environment.GetEnvironmentVariable("WEBHOOK_SECRET");

// inside your webhook handler
var eventNotification = client.ParseEventNotification(json, Request.Headers["Stripe-Signature"], webhookSecret);

if (eventNotification is V1BillingMeterErrorReportTriggeredEventNotification notif)
{
  // uses `context` automatically
  notif.fetchEvent();

  // pass context manually for other API requests
  client.V1.Invoices.List(null, new RequestOptions
  {
      StripeContext = notif.Context,
  });
}
```

#### Thin event handler (Acacia or Basil)

This code snippet is a webhook function configured to receive thin events across an organization, verify the signature, determine the originating account with the `context` field, and use that account’s API key for subsequent API calls.

#### Python

```python
import os
from flask import Flask, request, jsonify
from stripe import StripeClient
from stripe.events import V1BillingMeterErrorReportTriggeredEvent

app = Flask(__name__)

org_api_key = os.environ.get("STRIPE_API_KEY")
webhook_secret = os.environ.get("WEBHOOK_SECRET")
client = StripeClient(org_api_key)

account_api_keys = {
    "account_123": os.environ.get("ACCOUNT_123_API_KEY"),
    "account_456": os.environ.get("ACCOUNT_456_API_KEY"),
}

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        thin_event = client.parse_thin_event(payload, sig_header, webhook_secret)

        # Retrieve the event using the org client to inspect context
        event = client.v2.core.events.retrieve(thin_event.id)

        context = getattr(event, "context", None)
        if not context:
            return jsonify(error="Missing context"), 400

        account_key = account_api_keys.get(context)
        if not account_key:
            return jsonify(error="Unknown context"), 400

        account_client = StripeClient(account_key)
        full_event = account_client.v2.core.events.retrieve(thin_event.id)

        if isinstance(full_event, V1BillingMeterErrorReportTriggeredEvent):
            meter = full_event.fetch_related_object()
            meter_id = meter.id
            # Record the failures and alert your team
            # Add your logic here

        return jsonify(success=True), 200
    except Exception as e:
        return jsonify(error=str(e)), 400

if __name__ == "__main__":
    app.run(port=4242)
```

#### Ruby

```ruby
require "stripe"
require "sinatra"

api_key = ENV.fetch("STRIPE_API_KEY", nil)
webhook_secret = ENV.fetch("WEBHOOK_SECRET", nil)
client = Stripe::StripeClient.new(api_key)

account_api_keys = {
  "account_123" => ENV["ACCOUNT_123_API_KEY"],
  "account_456" => ENV["ACCOUNT_456_API_KEY"],
}

post "/webhook" do
  webhook_body = request.body.read
  sig_header = request.env["HTTP_STRIPE_SIGNATURE"]

  begin
    thin_event = client.parse_thin_event(webhook_body, sig_header, webhook_secret)
    event = client.v2.core.events.retrieve(thin_event.id)

    context = event.context
    halt 400 if context.nil?

    account_key = account_api_keys[context]
    halt 400 if account_key.nil?

    account_client = Stripe::StripeClient.new(account_key)
    full_event = account_client.v2.core.events.retrieve(thin_event.id)

    if full_event.instance_of? Stripe::V1BillingMeterErrorReportTriggeredEvent
      meter = full_event.fetch_related_object
      # Record the failures and alert your team
      # Add your logic here
    end

    status 200
  rescue => e
    status 400
  end
end
```

#### Node.js

```javascript
const express = require('express');
const {Stripe} = require('stripe');

const app = express();

const apiKey = process.env.STRIPE_API_KEY;
const webhookSecret = process.env.WEBHOOK_SECRET;
const client = new Stripe(apiKey);

const accountApiKeys = {
  account_123: process.env.ACCOUNT_123_API_KEY,
  account_456: process.env.ACCOUNT_456_API_KEY,
};

app.post('/webhook', express.raw({type: 'application/json'}), async (req, res) => {
  const sig = req.headers['stripe-signature'];

  try {
    const thinEvent = client.parseThinEvent(req.body, sig, webhookSecret);
    const event = await client.v2.core.events.retrieve(thinEvent.id);

    const context = event.context;
    if (!context) return res.status(400).send('Missing context');

    const accountKey = accountApiKeys[context];
    if (!accountKey) return res.status(400).send('Unknown context');

    const accountClient = new Stripe(accountKey);
    const fullEvent = await accountClient.v2.core.events.retrieve(thinEvent.id);

    if (fullEvent.type === 'v1.billing.meter.error_report_triggered') {
      const meter = await fullEvent.fetchRelatedObject();
      // Record the failures and alert your team
      // Add your logic here
    }

    res.sendStatus(200);
  } catch (err) {
    res.status(400).send(`Webhook Error: ${err.message}`);
  }
});

app.listen(4242);
```

#### Java

```java
import com.stripe.StripeClient;
import com.stripe.events.V1BillingMeterErrorReportTriggeredEvent;
import com.stripe.model.Event;
import com.stripe.model.ThinEvent;
import java.util.HashMap;
import java.util.Map;

public Object handle(Request request, Response response) {
  String apiKey = System.getenv("STRIPE_API_KEY");
  String webhookSecret = System.getenv("WEBHOOK_SECRET");
  StripeClient client = new StripeClient(apiKey);

  Map<String, String> accountApiKeys = new HashMap<>();
  accountApiKeys.put("account_123", System.getenv("ACCOUNT_123_API_KEY"));
  accountApiKeys.put("account_456", System.getenv("ACCOUNT_456_API_KEY"));

  try {
    String webhookBody = request.body();
    String sigHeader = request.headers("Stripe-Signature");
    ThinEvent thinEvent = client.parseThinEvent(webhookBody, sigHeader, webhookSecret);

    Event baseEvent = client.v2().core().events().retrieve(thinEvent.getId());
    String context = baseEvent.getContext();
    if (context == null || context.isEmpty()) {
      response.status(400);
      return "";
    }

    String accountKey = accountApiKeys.get(context);
    if (accountKey == null || accountKey.isEmpty()) {
      response.status(400);
      return "";
    }

    StripeClient accountClient = new StripeClient(accountKey);
    Event fullEvent = accountClient.v2().core().events().retrieve(thinEvent.getId());

    if (fullEvent instanceof V1BillingMeterErrorReportTriggeredEvent) {
      V1BillingMeterErrorReportTriggeredEvent ev = (V1BillingMeterErrorReportTriggeredEvent) fullEvent;
      Object meter = ev.fetchRelatedObject();
      // Record the failures and alert your team
      // Add your logic here
    }

    response.status(200);
    return "";
  } catch (Exception e) {
    response.status(400);
    return "";
  }
}
```

#### PHP

```php
<?php

require 'vendor/autoload.php';

$api_key = getenv('STRIPE_API_KEY');
$webhook_secret = getenv('WEBHOOK_SECRET');
$client = new \Stripe\StripeClient($api_key);

$accountApiKeys = [
  'account_123' => getenv('ACCOUNT_123_API_KEY'),
  'account_456' => getenv('ACCOUNT_456_API_KEY'),
];

$app = new \Slim\App();

$app->post('/webhook', function ($request, $response) use ($client, $webhook_secret, $accountApiKeys) {
    $webhook_body = $request->getBody()->getContents();
    $sig_header = $request->getHeaderLine('Stripe-Signature');

    try {
        $thin_event = $client->parseThinEvent($webhook_body, $sig_header, $webhook_secret);
        $event = $client->v2->core->events->retrieve($thin_event->id);

        $context = $event->context ?? null;
        if (!$context) return $response->withStatus(400);

        $accountKey = $accountApiKeys[$context] ?? null;
        if (!$accountKey) return $response->withStatus(400);

        $accountClient = new \Stripe\StripeClient($accountKey);
        $full_event = $accountClient->v2->core->events->retrieve($thin_event->id);

        if ($full_event instanceof \Stripe\\Events\\V1BillingMeterErrorReportTriggeredEvent) {
            $meter = $full_event->fetchRelatedObject();
            // Record the failures and alert your team
            // Add your logic here
        }

        return $response->withStatus(200);
    } catch (\Exception $e) {
        return $response->withStatus(400);
    }
});

$app->run();
```

#### Go

```go
package main

import (
  "io"
  "log/slog"
  "net/http"
  "os"

  "github.com/stripe/stripe-go/v82"
)

func main() {
  apiKey := os.Getenv("STRIPE_API_KEY")
  webhookSecret := os.Getenv("WEBHOOK_SECRET")
  client := stripe.NewClient(apiKey)

  accountApiKeys := map[string]string{
    "account_123": os.Getenv("ACCOUNT_123_API_KEY"),
    "account_456": os.Getenv("ACCOUNT_456_API_KEY"),
  }

  http.HandleFunc("/webhook", func(w http.ResponseWriter, req *http.Request) {
    defer req.Body.Close()
    payload, err := io.ReadAll(req.Body)
    if err != nil {
      slog.Error("read body", "error", err)
      w.WriteHeader(http.StatusInternalServerError)
      return
    }

    thinEvent, err := client.ParseThinEvent(payload, req.Header.Get("Stripe-Signature"), webhookSecret)
    if err != nil {
      w.WriteHeader(http.StatusBadRequest)
      return
    }

    baseEvent, err := client.V2.Core.Events.Retrieve(thinEvent.ID)
    if err != nil {
      w.WriteHeader(http.StatusInternalServerError)
      return
    }

    if baseEvent.Context == "" {
      w.WriteHeader(http.StatusBadRequest)
      return
    }

    accountKey, ok := accountApiKeys[baseEvent.Context]
    if !ok || accountKey == "" {
      w.WriteHeader(http.StatusBadRequest)
      return
    }

    accountClient := stripe.NewClient(accountKey)
    fullEvent, err := accountClient.V2.Core.Events.Retrieve(thinEvent.ID)
    if err != nil {
      w.WriteHeader(http.StatusInternalServerError)
      return
    }

    switch e := fullEvent.(type) {
    case *stripe.V1BillingMeterErrorReportTriggeredEvent:
      meter, err := e.FetchRelatedObject()
      if err == nil {
        _ = meter
        // Record the failures and alert your team
        // Add your logic here
      }
    }

    w.WriteHeader(http.StatusOK)
  })

  http.ListenAndServe(":4242", nil)
}
```

#### .NET

```csharp
using Microsoft.AspNetCore.Mvc;
using Stripe;

[ApiController]
[Route("/webhook")]
public class WebhookController : ControllerBase
{
    private readonly StripeClient _client;
    private readonly string _webhookSecret;
    private readonly Dictionary<string, string> _accountApiKeys;

    public WebhookController()
    {
        _client = new StripeClient(Environment.GetEnvironmentVariable("STRIPE_API_KEY"));
        _webhookSecret = Environment.GetEnvironmentVariable("WEBHOOK_SECRET");
        _accountApiKeys = new Dictionary<string, string>
        {
            { "account_123", Environment.GetEnvironmentVariable("ACCOUNT_123_API_KEY") },
            { "account_456", Environment.GetEnvironmentVariable("ACCOUNT_456_API_KEY") },
        };
    }

    [HttpPost]
    public async Task<IActionResult> Handle()
    {
        using var reader = new StreamReader(Request.Body);
        var json = await reader.ReadToEndAsync();

        try
        {
            var thinEvent = _client.ParseThinEvent(json, Request.Headers["Stripe-Signature"], _webhookSecret);
            var baseEvent = await _client.V2.Core.Events.GetAsync(thinEvent.Id);

            if (string.IsNullOrEmpty(baseEvent.Context))
            {
                return BadRequest();
            }

            if (!_accountApiKeys.TryGetValue(baseEvent.Context, out var accountKey) || string.IsNullOrEmpty(accountKey))
            {
                return BadRequest();
            }

            var accountClient = new StripeClient(accountKey);
            var fullEvent = await accountClient.V2.Core.Events.GetAsync(thinEvent.Id);

            if (fullEvent is V1BillingMeterErrorReportTriggeredEvent ev)
            {
                var meter = await ev.FetchRelatedObjectAsync();
                // Record the failures and alert your team
                // Add your logic here
            }

            return Ok();
        }
        catch
        {
            return BadRequest();
        }
    }
}
```

## Test your handler

Before you go-live with your webhook endpoint function, we recommend that you test your application integration. You can do so by configuring a local listener to send events to your local machine, and sending test events. You need to use the [CLI](https://docs.stripe.com/stripe-cli.md) to test.

#### Forward events to a local endpoint 

To forward events to your local endpoint, run the following command with the [CLI](https://docs.stripe.com/stripe-cli.md) to set up a local listener. The `--forward-to` flag sends all [Stripe events](https://docs.stripe.com/cli/trigger#trigger-event) in a [sandbox](https://docs.stripe.com/sandboxes.md) to your local webhook endpoint. Use the appropriate CLI commands below depending on whether you use [thin](https://docs.stripe.com/event-destinations.md#events-overview) or snapshot events.

#### Forward snapshot events

Use the following command to forward [snapshot events](https://docs.stripe.com/event-destinations.md#events-overview) to your local listener.

```bash
stripe listen --forward-to localhost:4242
```

#### Forward thin events

Use the following command to forward [thin events](https://docs.stripe.com/event-destinations.md#events-overview) to your local listener.

```bash
$ stripe listen --forward-thin-to localhost:4242 --thin-events "*"
```

> You can also run `stripe listen` to see events in [Stripe Shell](https://docs.stripe.com/stripe-shell/overview.md), although you won’t be able to forward events from the shell to your local endpoint.

Useful configurations to help you test with your local listener include the following:

- To disable HTTPS certificate verification, use the `--skip-verify` optional flag.
- To forward only specific events, use the `--events` optional flag and pass in a comma separated list of events.

#### Forward target snapshot events

Use the following command to forward target snapshot events to your local listener.

```bash
stripe listen --events payment_intent.created,customer.created,payment_intent.succeeded,checkout.session.completed,payment_intent.payment_failed \
  --forward-to localhost:4242
```

#### Forward target thin events

Use the following command to forward target thin events to your local listener.

```bash
stripe listen --thin-events v1.billing.meter.error_report_triggered,v1.billing.meter.no_meter_found \
  --forward-thin-to localhost:4242
```

- To forward events to your local webhook endpoint from the public webhook endpoint that you already registered on Stripe, use the `--load-from-webhooks-api` optional flag. It loads your registered endpoint, parses the path and its registered events, then appends the path to your local webhook endpoint in the `--forward-to path`.

#### Forward snapshot events from a public webhook endpoint

Use the following command to forward snapshot events from a public webhook endpoint to your local listener.

```bash
stripe listen --load-from-webhooks-api --forward-to localhost:4242
```

#### Forward thin events from a public webhook endpoint

Use the following command to forward thin events from a public webhook endpoint to your local listener.

```bash
stripe listen --load-from-webhooks-api --forward-thin-to localhost:4242
```

- To check webhook signatures, use the `{{WEBHOOK_SIGNING_SECRET}}` from the initial output of the listen command.

```output
Ready! Your webhook signing secret is '{{WEBHOOK_SIGNING_SECRET}}' (^C to quit)
```

#### Triggering test events 

To send test events, trigger an event type that your event destination is subscribed to by manually creating an object in the Stripe Dashboard. Learn how to trigger events with [Stripe for VS Code](https://docs.stripe.com/stripe-vscode.md).

#### Trigger a snapshot event

You can use the following command in either [Stripe Shell](https://docs.stripe.com/stripe-shell/overview.md) or [Stripe CLI](https://docs.stripe.com/stripe-cli.md). This example triggers a `payment_intent.succeeded` event:

```bash
stripe trigger payment_intent.succeeded
Running fixture for: payment_intent
Trigger succeeded! Check dashboard for event details.
```

#### Trigger a thin event

You can use the following command in the [Stripe CLI](https://docs.stripe.com/stripe-cli.md). This example triggers a `outbound_payment.posted` event:

```bash
stripe preview trigger outbound_payment.posted
Setting up fixture for: finaddr_info
Running fixture for: finaddr_info
Setting up fixture for: create_recipient
Running fixture for: create_recipient
Setting up fixture for: create_destination
Running fixture for: create_destination
Setting up fixture for: create_outbound_payment
Running fixture for: create_outbound_payment
```

## Register your endpoint

After testing your webhook endpoint function, use the [API](https://docs.stripe.com/api/v2/event-destinations.md) or the **Webhooks** tab in Workbench to register your webhook endpoint’s accessible URL so Stripe knows where to deliver events. You can register up to 16 webhook endpoints with Stripe. Registered webhook endpoints must be publicly accessible **HTTPS** URLs.

#### Webhook URL format 

The URL format to register a webhook endpoint is:

```
https://<your-website>/<your-webhook-endpoint>
```

For example, if your domain is `https://mycompanysite.com` and the route to your webhook endpoint is `@app.route('/stripe_webhooks', methods=['POST'])`, specify `https://mycompanysite.com/stripe_webhooks` as the **Endpoint URL**.

#### Create an event destination for your webhook endpoint 

Create an event destination using Workbench in the Dashboard or programmatically with the [API](https://docs.stripe.com/api/v2/event-destinations.md). You can register up to 16 event destinations on each Stripe account.

#### Dashboard

To create a new webhook endpoint in the Dashboard:

1. Open the [Webhooks](https://dashboard.stripe.com/webhooks) tab in Workbench.
1. Click **Create an event destination**.
1. Select where you want to receive events from. Stripe supports two types of configurations: **Your account** and [Connected accounts](https://docs.stripe.com/connect.md). Select **Account** to listen to events from your own account. If you created a [Connect application](https://docs.stripe.com/connect.md) and want to listen to events from your connected accounts, select **Connected accounts**.

> #### Listen to events from an organization webhook endpoint
> 
> If you create a webhook endpoint in an [organization account](https://docs.stripe.com/get-started/account/orgs.md), select **Accounts** to listen to events from accounts in your organization. If you have [Connect platforms](https://docs.stripe.com/connect.md) as members of your organizations and want to listen to events from the all the platforms’ connected accounts, select **Connected accounts**.

1. Select the API version for the [events object](https://docs.stripe.com/api/events.md) you want to consume.
1. Select the [event types](https://docs.stripe.com/api/events/types.md) that you want to send to a webhook endpoint.
1. Select **Continue**, then select **Webhook endpoint** as the destination type.
1. Click **Continue**, then provide the **Endpoint URL** and an optional description for the webhook.
![Register a new webhook using the Webhooks tab](https://b.stripecdn.com/docs-statics-srv/assets/create-webhook.f728025897e9e4ca2ba623abe34995a0.png)

Register a new webhook using the **Webhooks** tab

#### API

You can create a new event destination that notifies you when a [usage-based billing](https://docs.stripe.com/billing/subscriptions/usage-based.md) validation error is triggered using the [API](https://docs.stripe.com/api/v2/event-destinations.md).

If you’ve created a [Connect application](https://docs.stripe.com/connect.md) and want to listen to your connected accounts, use the [events_from](https://docs.stripe.com/api/v2/event-destinations/create.md#v2_create_event_destinations-events_from) parameter and set its enum value to `accounts`.

```curl
curl -X POST https://api.stripe.com/v2/core/event_destinations \
  -H "Authorization: Bearer <<YOUR_SECRET_KEY>>" \
  -H "Stripe-Version: {{STRIPE_API_VERSION}}" \
  --json '{
    "name": "My event destination",
    "description": "This is my event destination, I like it a lot",
    "type": "webhook_endpoint",
    "event_payload": "thin",
    "enabled_events": [
        "v1.billing.meter.error_report_triggered"
    ],
    "webhook_endpoint": {
        "url": "https://example.com/my/webhook/endpoint"
    }
  }'
```

```cli
stripe v2 core event_destinations create  \
  --name="My event destination" \
  --description="This is my event destination, I like it a lot" \
  --type=webhook_endpoint \
  --event-payload=thin \
  --enabled-events="v1.billing.meter.error_report_triggered" \
  --webhook-endpoint.url="https://example.com/my/webhook/endpoint"
```

```ruby
# Set your secret key. Remember to switch to your live secret key in production.
# See your keys here: https://dashboard.stripe.com/apikeys
client = Stripe::StripeClient.new("<<YOUR_SECRET_KEY>>")

event_destination = client.v2.core.event_destinations.create({
  name: 'My event destination',
  description: 'This is my event destination, I like it a lot',
  type: 'webhook_endpoint',
  event_payload: 'thin',
  enabled_events: ['v1.billing.meter.error_report_triggered'],
  webhook_endpoint: {url: 'https://example.com/my/webhook/endpoint'},
})
```

```python
# Set your secret key. Remember to switch to your live secret key in production.
# See your keys here: https://dashboard.stripe.com/apikeys
client = StripeClient("<<YOUR_SECRET_KEY>>")

event_destination = client.v2.core.event_destinations.create({
  "name": "My event destination",
  "description": "This is my event destination, I like it a lot",
  "type": "webhook_endpoint",
  "event_payload": "thin",
  "enabled_events": ["v1.billing.meter.error_report_triggered"],
  "webhook_endpoint": {"url": "https://example.com/my/webhook/endpoint"},
})
```

```php
// Set your secret key. Remember to switch to your live secret key in production.
// See your keys here: https://dashboard.stripe.com/apikeys
$stripe = new \Stripe\StripeClient('<<YOUR_SECRET_KEY>>');

$eventDestination = $stripe->v2->core->eventDestinations->create([
  'name' => 'My event destination',
  'description' => 'This is my event destination, I like it a lot',
  'type' => 'webhook_endpoint',
  'event_payload' => 'thin',
  'enabled_events' => ['v1.billing.meter.error_report_triggered'],
  'webhook_endpoint' => ['url' => 'https://example.com/my/webhook/endpoint'],
]);
```

```java
// Set your secret key. Remember to switch to your live secret key in production.
// See your keys here: https://dashboard.stripe.com/apikeys
StripeClient client = new StripeClient("<<YOUR_SECRET_KEY>>");

EventDestinationCreateParams params =
  EventDestinationCreateParams.builder()
    .setName("My event destination")
    .setDescription("This is my event destination, I like it a lot")
    .setType(EventDestinationCreateParams.Type.WEBHOOK_ENDPOINT)
    .setEventPayload(EventDestinationCreateParams.EventPayload.THIN)
    .addEnabledEvent("v1.billing.meter.error_report_triggered")
    .setWebhookEndpoint(
      EventDestinationCreateParams.WebhookEndpoint.builder()
        .setUrl("https://example.com/my/webhook/endpoint")
        .build()
    )
    .build();

EventDestination eventDestination = client.v2().core().eventDestinations().create(params);
```

```node
// Set your secret key. Remember to switch to your live secret key in production.
// See your keys here: https://dashboard.stripe.com/apikeys
const stripe = require('stripe')('<<YOUR_SECRET_KEY>>');

const eventDestination = await stripe.v2.core.eventDestinations.create({
  name: 'My event destination',
  description: 'This is my event destination, I like it a lot',
  type: 'webhook_endpoint',
  event_payload: 'thin',
  enabled_events: ['v1.billing.meter.error_report_triggered'],
  webhook_endpoint: {
    url: 'https://example.com/my/webhook/endpoint',
  },
});
```

```go
// Set your secret key. Remember to switch to your live secret key in production.
// See your keys here: https://dashboard.stripe.com/apikeys
sc := stripe.NewClient("<<YOUR_SECRET_KEY>>")
params := &stripe.V2CoreEventDestinationCreateParams{
  Name: stripe.String("My event destination"),
  Description: stripe.String("This is my event destination, I like it a lot"),
  Type: stripe.String("webhook_endpoint"),
  EventPayload: stripe.String("thin"),
  EnabledEvents: []*string{stripe.String("v1.billing.meter.error_report_triggered")},
  WebhookEndpoint: &stripe.V2CoreEventDestinationCreateWebhookEndpointParams{
    URL: stripe.String("https://example.com/my/webhook/endpoint"),
  },
}
result, err := sc.V2CoreEventDestinations.Create(context.TODO(), params)
```

```dotnet
// Set your secret key. Remember to switch to your live secret key in production.
// See your keys here: https://dashboard.stripe.com/apikeys
var options = new Stripe.V2.Core.EventDestinationCreateOptions
{
    Name = "My event destination",
    Description = "This is my event destination, I like it a lot",
    Type = "webhook_endpoint",
    EventPayload = "thin",
    EnabledEvents = new List<string> { "v1.billing.meter.error_report_triggered" },
    WebhookEndpoint = new Stripe.V2.Core.EventDestinationCreateWebhookEndpointOptions
    {
        Url = "https://example.com/my/webhook/endpoint",
    },
};
var client = new StripeClient("<<YOUR_SECRET_KEY>>");
var service = client.V2.Core.EventDestinations;
Stripe.V2.Core.EventDestination eventDestination = service.Create(options);
```

> [Workbench](https://docs.stripe.com/workbench.md) replaces the existing [Developers Dashboard](https://docs.stripe.com/development/dashboard.md). If you’re still using the Developers Dashboard, see how to [create a new webhook endpoint](https://docs.stripe.com/development/dashboard/webhooks.md).

## Secure your endpoint

After confirming that your endpoint works as expected, secure it by implementing [webhook best practices](https://docs.stripe.com/webhooks.md#best-practices).

You need to secure your integration by making sure your handler verifies that all webhook requests are generated by Stripe. You can verify webhook signatures using our official libraries or verify them manually.

#### Verify with official libraries (recommended)

### Verify webhook signatures with official libraries

We recommend using our official libraries to verify signatures. You perform the verification by providing the event payload, the `Stripe-Signature` header, and the endpoint’s secret. If verification fails, you get an error.

If you get a signature verification error, read our guide about [troubleshooting it](https://docs.stripe.com/webhooks/signature.md).

> Stripe requires the raw body of the request to perform signature verification. If you’re using a framework, make sure it doesn’t manipulate the raw body. Any manipulation to the raw body of the request causes the verification to fail.

#### Ruby

```ruby

# Set your secret key. Remember to switch to your live secret key in production.
# See your keys here: https://dashboard.stripe.com/apikeys
Stripe.api_key = '<<YOUR_SECRET_KEY>>'

require 'stripe'
require 'sinatra'

# If you are testing your webhook locally with the Stripe CLI you
# can find the endpoint's secret by running `stripe listen`
# Otherwise, find your endpoint's secret in your webhook settings in
# the Developer Dashboardendpoint_secret = 'whsec_...'

# Using the Sinatra framework
set :port, 4242

post '/my/webhook/url' do
  payload = request.body.readsig_header = request.env['HTTP_STRIPE_SIGNATURE']
  event = nil

  beginevent = Stripe::Webhook.construct_event(
      payload, sig_header, endpoint_secret
    )
  rescue JSON::ParserError => e
    # Invalid payload
    puts "Error parsing payload: #{e.message}"
    status 400
    return
  rescue Stripe::SignatureVerificationError => e# Invalid signature
    puts "Error verifying webhook signature: #{e.message}"
    status 400
    return
  end

  # Handle the event
  case event.type
  when 'payment_intent.succeeded'
    payment_intent = event.data.object # contains a Stripe::PaymentIntent
    puts 'PaymentIntent was successful!'
  when 'payment_method.attached'
    payment_method = event.data.object # contains a Stripe::PaymentMethod
    puts 'PaymentMethod was attached to a Customer!'
  # ... handle other event types
  else
    puts "Unhandled event type: #{event.type}"
  end

  status 200
end
```

#### Python

```python

# Set your secret key. Remember to switch to your live secret key in production.
# See your keys here: https://dashboard.stripe.com/apikeys
stripe.api_key = '<<YOUR_SECRET_KEY>>'

from django.http import HttpResponse

# If you are testing your webhook locally with the Stripe CLI you
# can find the endpoint's secret by running `stripe listen`
# Otherwise, find your endpoint's secret in your webhook settings in the Developer Dashboardendpoint_secret = 'whsec_...'

# Using Django
@csrf_exempt
def my_webhook_view(request):
  payload = request.bodysig_header = request.META['HTTP_STRIPE_SIGNATURE']
  event = None

  try:event = stripe.Webhook.construct_event(
      payload, sig_header, endpoint_secret
    )
  except ValueError as e:
    # Invalid payload
    print('Error parsing payload: {}'.format(str(e)))
    return HttpResponse(status=400)except stripe.error.SignatureVerificationError as e:
    # Invalid signature
    print('Error verifying webhook signature: {}'.format(str(e)))
    return HttpResponse(status=400)

  # Handle the event
  if event.type == 'payment_intent.succeeded':
    payment_intent = event.data.object # contains a stripe.PaymentIntent
    print('PaymentIntent was successful!')
  elif event.type == 'payment_method.attached':
    payment_method = event.data.object # contains a stripe.PaymentMethod
    print('PaymentMethod was attached to a Customer!')
  # ... handle other event types
  else:
    print('Unhandled event type {}'.format(event.type))

  return HttpResponse(status=200)
```

#### PHP

```php

// Set your secret key. Remember to switch to your live secret key in production.
// See your keys here: https://dashboard.stripe.com/apikeys
\Stripe\Stripe::setApiKey('<<YOUR_SECRET_KEY>>');

// If you are testing your webhook locally with the Stripe CLI you
// can find the endpoint's secret by running `stripe listen`
// Otherwise, find your endpoint's secret in your webhook settings in the Developer Dashboard$endpoint_secret = 'whsec_...';

$payload = @file_get_contents('php://input');
$sig_header = $_SERVER['HTTP_STRIPE_SIGNATURE'];
$event = null;

try {$event = \Stripe\Webhook::constructEvent(
        $payload, $sig_header, $endpoint_secret
    );
} catch(\UnexpectedValueException $e) {
    // Invalid payload
  http_response_code(400);
  echo json_encode(['Error parsing payload: ' => $e->getMessage()]);
  exit();} catch(\Stripe\Exception\SignatureVerificationException $e) {
    // Invalid signature
    http_response_code(400);
    echo json_encode(['Error verifying webhook signature: ' => $e->getMessage()]);
    exit();
}

// Handle the event
switch ($event->type) {
    case 'payment_intent.succeeded':
        $paymentIntent = $event->data->object; // contains a \Stripe\PaymentIntent
        handlePaymentIntentSucceeded($paymentIntent);
        break;
    case 'payment_method.attached':
        $paymentMethod = $event->data->object; // contains a \Stripe\PaymentMethod
        handlePaymentMethodAttached($paymentMethod);
        break;
    // ... handle other event types
    default:
        echo 'Received unknown event type ' . $event->type;
}

http_response_code(200);
```

#### Java

```java

// Set your secret key. Remember to switch to your live secret key in production.
// See your keys here: https://dashboard.stripe.com/apikeys
Stripe.apiKey = "<<YOUR_SECRET_KEY>>";

import com.stripe.Stripe;
import com.stripe.model.StripeObject;
import com.stripe.net.ApiResource;
import com.stripe.net.Webhook;
import com.stripe.model.Event;
import com.stripe.model.EventDataObjectDeserializer;
import com.stripe.model.PaymentIntent;
import com.stripe.exception.SignatureVerificationException;

// If you are testing your webhook locally with the Stripe CLI you
// can find the endpoint's secret by running `stripe listen`
// Otherwise, find your endpoint's secret in your webhook settings in the Developer DashboardString endpointSecret = "whsec_...";

// Using the Spark framework
public Object handle(Request request, Response response) {
  String payload = request.body();String sigHeader = request.headers("Stripe-Signature");
  Event event = null;

  try {event = Webhook.constructEvent(
      payload, sigHeader, endpointSecret
    );
  } catch (JsonSyntaxException e) {
    // Invalid payload
    System.out.println("Error parsing payload: " + e.getMessage());
    response.status(400);
    return gson.toJson(new ErrorResponse(e.getMessage()));} catch (SignatureVerificationException e) {
    // Invalid signature
    System.out.println("Error verifying webhook signature: " + e.getMessage());
    response.status(400);
    return gson.toJson(new ErrorResponse(e.getMessage()));
  }

  // Deserialize the nested object inside the event
  EventDataObjectDeserializer dataObjectDeserializer = event.getDataObjectDeserializer();
  StripeObject stripeObject = null;
  if (dataObjectDeserializer.getObject().isPresent()) {
    stripeObject = dataObjectDeserializer.getObject().get();
  } else {
    // Deserialization failed, probably due to an API version mismatch.
    // Refer to the Javadoc documentation on `EventDataObjectDeserializer` for
    // instructions on how to handle this case, or return an error here.
  }

  // Handle the event
  switch (event.getType()) {
    case "payment_intent.succeeded":
      PaymentIntent paymentIntent = (PaymentIntent) stripeObject;
      System.out.println("PaymentIntent was successful!");
      break;
    case "payment_method.attached":
      PaymentMethod paymentMethod = (PaymentMethod) stripeObject;
      System.out.println("PaymentMethod was attached to a Customer!");
      break;
    // ... handle other event types
    default:
      System.out.println("Unhandled event type: " + event.getType());
  }

  response.status(200);
  return "";
}
```

#### Node.js

```javascript

// Set your secret key. Remember to switch to your live secret key in production.
// See your keys here: https://dashboard.stripe.com/apikeys
const stripe = require('stripe')('<<YOUR_SECRET_KEY>>');

// If you are testing your webhook locally with the Stripe CLI you
// can find the endpoint's secret by running `stripe listen`
// Otherwise, find your endpoint's secret in your webhook settings in the Developer Dashboardconst endpointSecret = 'whsec_...';

// This example uses Express to receive webhooks
const express = require('express');

const app = express();

// Match the raw body to content type application/json
app.post('/webhook', express.raw({type: 'application/json'}), (request, response) => {const sig = request.headers['stripe-signature'];

  let event;

  try {event = stripe.webhooks.constructEvent(request.body, sig, endpointSecret);
  }catch (err) {
    response.status(400).send(`Webhook Error: ${err.message}`);
  }

  // Handle the event
  switch (event.type) {
    case 'payment_intent.succeeded':
      const paymentIntent = event.data.object;
      console.log('PaymentIntent was successful!');
      break;
    case 'payment_method.attached':
      const paymentMethod = event.data.object;
      console.log('PaymentMethod was attached to a Customer!');
      break;
    // ... handle other event types
    default:
      console.log(`Unhandled event type ${event.type}`);
  }

  // Return a response to acknowledge receipt of the event
  response.json({received: true});
});

app.listen(4242, () => console.log('Running on port 4242'));
```

#### Go

```go

// Set your secret key. Remember to switch to your live secret key in production.
// See your keys here: https://dashboard.stripe.com/apikeys
stripe.Key = "<<YOUR_SECRET_KEY>>"

http.HandleFunc("/webhook", func(w http.ResponseWriter, req *http.Request) {
    const MaxBodyBytes = int64(65536)
    req.Body = http.MaxBytesReader(w, req.Body, MaxBodyBytes)
    payload, err := ioutil.ReadAll(req.Body)
    if err != nil {
        fmt.Fprintf(os.Stderr, "Error reading request body: %v\n", err)
        w.WriteHeader(http.StatusServiceUnavailable)
        return
    }

    // If you are testing your webhook locally with the Stripe CLI you
    // can find the endpoint's secret by running `stripe listen`
    // Otherwise, find your endpoint's secret in your webhook settings
    // in the Developer DashboardendpointSecret := "whsec_...";

    // Pass the request body and Stripe-Signature header to ConstructEvent, along
    // with the webhook signing key.event, err := webhook.ConstructEvent(payload, req.Header.Get("Stripe-Signature"),
        endpointSecret)
if err != nil {
        fmt.Fprintf(os.Stderr, "Error verifying webhook signature: %v\n", err)
        w.WriteHeader(http.StatusBadRequest) // Return a 400 error on a bad signature
        return
    }

    // Unmarshal the event data into an appropriate struct depending on its Type
    switch event.Type {
    case "payment_intent.succeeded":
        var paymentIntent stripe.PaymentIntent
        err := json.Unmarshal(event.Data.Raw, &paymentIntent)
        if err != nil {
            fmt.Fprintf(os.Stderr, "Error parsing webhook JSON: %v\n", err)
            w.WriteHeader(http.StatusBadRequest)
            return
        }
        fmt.Println("PaymentIntent was successful!")
    case "payment_method.attached":
        var paymentMethod stripe.PaymentMethod
        err := json.Unmarshal(event.Data.Raw, &paymentMethod)
        if err != nil {
            fmt.Fprintf(os.Stderr, "Error parsing webhook JSON: %v\n", err)
            w.WriteHeader(http.StatusBadRequest)
            return
        }
        fmt.Println("PaymentMethod was attached to a Customer!")
    // ... handle other event types
    default:
        fmt.Fprintf(os.Stderr, "Unhandled event type: %s\n", event.Type)
    }

    w.WriteHeader(http.StatusOK)
})
```

#### .NET

```dotnet

// Set your secret key. Remember to switch to your live secret key in production.
// See your keys here: https://dashboard.stripe.com/apikeys
StripeConfiguration.ApiKey = "<<YOUR_SECRET_KEY>>";

using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Stripe;

namespace workspace.Controllers
{
    [Route("api/[controller]")]
    public class StripeWebHook : Controller
    {
        // If you are testing your webhook locally with the Stripe CLI you
        // can find the endpoint's secret by running `stripe listen`
        // Otherwise, find your endpoint's secret in your webhook settings
        // in the Developer Dashboardconst string endpointSecret = "whsec_...";

        [HttpPost]
        public async Task<IActionResult> Index()
        {
            var json = await new StreamReader(HttpContext.Request.Body).ReadToEndAsync();

            try
            {var stripeEvent = EventUtility.ConstructEvent(json,
                    Request.Headers["Stripe-Signature"], endpointSecret);

                // Handle the event
                // If on SDK version < 46, use class Events instead of EventTypes
                if (stripeEvent.Type == EventTypes.PaymentIntentSucceeded)
                {
                    var paymentIntent = stripeEvent.Data.Object as PaymentIntent;
                    Console.WriteLine("PaymentIntent was successful!");
                }
                else if (stripeEvent.Type == EventTypes.PaymentMethodAttached)
                {
                    var paymentMethod = stripeEvent.Data.Object as PaymentMethod;
                    Console.WriteLine("PaymentMethod was attached to a Customer!");
                }
                // ... handle other event types
                else
                {
                    Console.WriteLine("Unhandled event type: {0}", stripeEvent.Type);
                }

                return Ok();
            }catch (StripeException e)
            {
              return BadRequest(e.Message);
            }
        }
    }
}
```

#### Verify manually

### Verify webhook signatures manually 

Although we recommend that you use our official libraries to verify webhook event signatures, you can create a custom solution by following this section.

The `Stripe-Signature` header included in each signed event contains a timestamp and one or more signatures that you must verify. The timestamp has a `t=` prefix, and each signature has a *scheme* prefix. Schemes start with `v`, followed by an integer. Currently, the only valid live signature scheme is `v1`. To aid with testing, Stripe sends an additional signature with a fake `v0` scheme, for test events.

```
Stripe-Signature:
t=1492774577,
v1=5257a869e7ecebeda32affa62cdca3fa51cad7e77a0e56ff536d0ce8e108d8bd,
v0=6ffbb59b2300aae63f272406069a9788598b792a944a07aba816edb039989a39
```

> We provide newlines for clarity, but a real `Stripe-Signature` header is on a single line.

Stripe generates signatures using a hash-based message authentication code ([HMAC](https://en.wikipedia.org/wiki/Hash-based_message_authentication_code)) with [SHA-256](https://en.wikipedia.org/wiki/SHA-2). To prevent [downgrade attacks](https://en.wikipedia.org/wiki/Downgrade_attack), ignore all schemes that aren’t `v1`.

You can have multiple signatures with the same scheme-secret pair when you [roll an endpoint’s secret](https://docs.stripe.com/webhooks.md#roll-endpoint-secrets), and keep the previous secret active for up to 24 hours. During this time, your endpoint has multiple active secrets and Stripe generates one signature for each secret.

To create a manual solution for verifying signatures, you must complete the following steps:

#### Step 1: Extract the timestamp and signatures from the header 

Split the header using the `,` character as the separator to get a list of elements. Then split each element using the `=` character as the separator to get a prefix and value pair.

The value for the prefix `t` corresponds to the timestamp, and `v1` corresponds to the signature (or signatures). You can discard all other elements.

#### Step 2: Prepare the `signed_payload` string 

The `signed_payload` string is created by concatenating:

- The timestamp (as a string)
- The character `.`
- The actual JSON payload (that is, the request body)

#### Step 3: Determine the expected signature 

Compute an HMAC with the SHA256 hash function. Use the endpoint’s signing secret as the key, and use the `signed_payload` string as the message.

#### Step 4: Compare the signatures 

Compare the signature (or signatures) in the header to the expected signature. For an equality match, compute the difference between the current timestamp and the received timestamp, then decide if the difference is within your tolerance.

To protect against timing attacks, use a constant-time-string comparison to compare the expected signature to each of the received signatures.

## Debug webhook integrations 

Multiple types of issues can occur when delivering events to your webhook endpoint:

- Stripe might not be able to deliver an event to your webhook endpoint.
- Your webhook endpoint might have an SSL issue.
- Your network connectivity is intermittent.
- Your webhook endpoint isn’t receiving events that you expect to receive.

### View event deliveries 

You can also use the [Stripe CLI](https://docs.stripe.com/stripe-cli.md) to [listen for events](https://docs.stripe.com/webhooks.md#test-webhook) directly in your terminal.

To view event deliveries, select the webhook endpoint under **Webhooks**, then select the **Events** tab.

The **Events** tab provides a list of events and whether they’re `Delivered`, `Pending`, or `Failed`. Click an event to view metadata, including the HTTP status code of the delivery attempt and the time of pending future deliveries.

### Fix HTTP status codes

When an event displays a status code of `200`, it indicates successful delivery to the webhook endpoint. You might also receive a status code other than `200`. View the table below for a list of common HTTP status codes and recommended solutions.

| Pending webhook status              | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Fix                                                                                                                                 |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| (Unable to connect) ERR             | We’re unable to establish a connection to the destination server.                                                                                                                                                                                                                                                                                                                                                                                                                          | Make sure that your host domain is publicly accessible to the internet.                                                             |
| (`302`) ERR (or other `3xx` status) | The destination server attempted to redirect the request to another location. We consider redirect responses to webhook requests as failures.                                                                                                                                                                                                                                                                                                                                              | Set the webhook endpoint destination to the URL resolved by the redirect.                                                           |
| (`400`) ERR (or other `4xx` status) | The destination server can’t or won’t process the request. This might occur when the server detects an error (`400`), when the destination URL has access restrictions, (`401`, `403`), or when the destination URL doesn’t exist (`404`).                                                                                                                                                                                                                                                 | - Make sure that your endpoint is publicly accessible to the internet.
  - Make sure that your endpoint accepts a POST HTTP method. |
| (`500`) ERR (or other `5xx` status) | The destination server encountered an error while processing the request.                                                                                                                                                                                                                                                                                                                                                                                                                  | Review your application’s logs to understand why it’s returning a `500` error.                                                      |
| (TLS error) ERR                     | We couldn’t establish a secure connection to the destination server. Issues with the SSL/TLS certificate or an intermediate certificate in the destination server’s certificate chain usually cause these errors. Stripe requires *TLS* (TLS refers to the process of securely transmitting data between the client—the app or browser that your customer is using—and your server. This was originally performed using the SSL (Secure Sockets Layer) protocol) version `v1.2` or higher. | Perform an [SSL server test](https://www.ssllabs.com/ssltest/) to find issues that might cause this error.                          |
| (Timed out) ERR                     | The destination server took too long to respond to the webhook request.                                                                                                                                                                                                                                                                                                                                                                                                                    | Make sure you defer complex logic and return a successful response immediately in your webhook handling code.                       |

## Event delivery behaviors 

This section helps you understand different behaviors to expect regarding how Stripe sends events to your webhook endpoint.

### Automatic retries

Stripe attempts to deliver events to your destination for up to three days with an exponential back off in live mode. View when the next retry will occur, if applicable, in your event destination’s **Event deliveries** tab. We retry event deliveries created in a sandbox three times over the course of a few hours. If your destination has been disabled or deleted when we attempt a retry, we prevent future retries of that event. However, if you disable and then re-enable the event destination before we’re able to retry, you still see future retry attempts.

### Manual retries

There are two ways to manually retry events:

- In the Stripe Dashboard, click **Resend** when looking at a specific event. This works for up to 15 days after the event creation.
- With the [Stripe CLI](https://docs.stripe.com/cli/events/resend), run the `stripe events resend <event_id> --webhook-endpoint=<endpoint_id>` command. This works for up to 30 days after the event creation.

Manually resending an event that had previous delivery failures to a webhook endpoint doesn’t dismiss Stripe’s [automatic retry behavior](https://docs.stripe.com/webhooks.md#automatic-retries). Automatic retries still happen until you respond to one of them with a `2xx` status code.

### Event ordering

Stripe doesn’t guarantee the delivery of events in the order that they’re generated. For example, creating a subscription might generate the following events:

- `customer.subscription.created`
- `invoice.created`
- `invoice.paid`
- `charge.created` (if there’s a charge)

Make sure that your event destination isn’t dependent on receiving events in a specific order. Be prepared to manage their delivery appropriately. You can also use the API to retrieve any missing objects. For example, you can retrieve the invoice, charge, and subscription objects with the information from `invoice.paid` if you receive this event first.

### API versioning

The API version in your account settings when the event occurs dictates the API version, and therefore the structure of an [Event](https://docs.stripe.com/api/events.md) sent to your destination. For example, if your account is set to an older API version, such as 2015-02-16, and you change the API version for a specific request with [versioning](https://docs.stripe.com/api.md#versioning), the [Event](https://docs.stripe.com/api/events.md) object generated and sent to your destination is still based on the 2015-02-16 API version. You can’t change [Event](https://docs.stripe.com/api/events.md) objects after creation. For example, if you update a charge, the original charge event remains unchanged. As a result, subsequent updates to your account’s API version don’t retroactively alter existing [Event](https://docs.stripe.com/api/events.md) objects. Retrieving an older [Event](https://docs.stripe.com/api/events.md) by calling `/v1/events` using a newer API version also has no impact on the structure of the received event. You can set test event destinations to either your default API version or the latest API version. The [Event](https://docs.stripe.com/api/events.md) sent to the destination is structured for the event destination’s specified version.

## Best practices for using webhooks 

Review these best practices to make sure your webhook endpoints remain secure and function well with your integration.

### Handle duplicate events

Webhook endpoints might occasionally receive the same event more than once. You can guard against duplicated event receipts by logging the [event IDs](https://docs.stripe.com/api/events/object.md#event_object-id) you’ve processed, and then not processing already-logged events.

In some cases, two separate Event objects are generated and sent. To identify these duplicates, use the ID of the object in `data.object` along with the `event.type`.

### Only listen to event types your integration requires

Configure your webhook endpoints to receive only the types of events required by your integration. Listening for extra events (or all events) puts undue strain on your server and we don’t recommend it.

You can [change the events](https://docs.stripe.com/api/webhook_endpoints/update.md#update_webhook_endpoint-enabled_events) that a webhook endpoint receives in the Dashboard or with the API.

### Handle events asynchronously

Configure your handler to process incoming events with an asynchronous queue. You might encounter scalability issues if you choose to process events synchronously. Any large spike in webhook deliveries (for example, during the beginning of the month when all subscriptions renew) might overwhelm your endpoint hosts.

Asynchronous queues allow you to process the concurrent events at a rate your system can support.

### Exempt webhook route from CSRF protection 

If you’re using Rails, Django, or another web framework, your site might automatically check that every POST request contains a *CSRF token*. This is an important security feature that helps protect you and your users from [cross-site request forgery](https://www.owasp.org/index.php/Cross-Site_Request_Forgery_\(CSRF\)) attempts. However, this security measure might also prevent your site from processing legitimate events. If so, you might need to exempt the webhooks route from CSRF protection.

#### Rails

```ruby
class StripeController < ApplicationController
  # If your controller accepts requests other than Stripe webhooks,
  # you'll probably want to use `protect_from_forgery` to add CSRF
  # protection for your application. But don't forget to exempt
  # your webhook route!
  protect_from_forgery except: :webhook

  def webhook
    # Process webhook data in `params`
  end
end
```

#### Django

```python
import json

# Webhooks are always sent as HTTP POST requests, so ensure
# that only POST requests reach your webhook view by
# decorating `webhook()` with `require_POST`.
#
# To ensure that the webhook view can receive webhooks,
# also decorate `webhook()` with `csrf_exempt`.
@require_POST
@csrf_exempt
def webhook(request):
  # Process webhook data in `request.body`
```

### Receive events with an HTTPS server

If you use an HTTPS URL for your webhook endpoint (required in live mode), Stripe validates that the connection to your server is secure before sending your webhook data. For this to work, your server must be correctly configured to support HTTPS with a valid server certificate. Stripe webhooks support only *TLS* (TLS refers to the process of securely transmitting data between the client—the app or browser that your customer is using—and your server. This was originally performed using the SSL (Secure Sockets Layer) protocol) versions v1.2 and v1.3.

### Roll endpoint signing secrets periodically 

The secret used for verifying that events come from Stripe is modifiable in the **Webhooks** tab in Workbench. To keep them safe, we recommend that you roll (change) secrets periodically, or when you suspect a compromised secret.

To roll a secret:

1. Click each endpoint in the Workbench **Webhooks** tab that you want to roll the secret for.
1. Navigate to the overflow menu (⋯) and click **Roll secret**. You can choose to immediately expire the current secret or delay its expiration for up to 24 hours to allow yourself time to update the verification code on your server. During this time, multiple secrets are active for the endpoint. Stripe generates one signature per secret until expiration.

### Verify events are sent from Stripe 

Stripe sends webhook events from a set list of IP addresses. Only trust events coming from these [IP addresses](https://docs.stripe.com/ips.md).

Also verify webhook signatures to confirm that Stripe sent the received events. Stripe signs webhook events it sends to your endpoints by including a signature in each event’s `Stripe-Signature` header. This allows you to verify that the events were sent by Stripe, not by a third party. You can verify signatures either using our [official libraries](https://docs.stripe.com/webhooks.md#verify-official-libraries), or [verify manually](https://docs.stripe.com/webhooks.md#verify-manually) using your own solution.

The following section describes how to verify webhook signatures:

1. Retrieve your endpoint’s secret.
1. Verify the signature.

#### Retrieving your endpoint’s secret 

Use Workbench and go to the **Webhooks** tab to view all your endpoints. Select an endpoint that you want to obtain the secret for, then click **Click to reveal**.

Stripe generates a unique secret key for each endpoint. If you use the same endpoint for both [test and live API keys](https://docs.stripe.com/keys.md#test-live-modes), the secret is different for each one. Additionally, if you use multiple endpoints, you must obtain a secret for each one you want to verify signatures on. After this setup, Stripe starts to sign each webhook it sends to the endpoint.

### Preventing replay attacks 

A [replay attack](https://en.wikipedia.org/wiki/Replay_attack) is when an attacker intercepts a valid payload and its signature, then re-transmits them. To mitigate such attacks, Stripe includes a timestamp in the `Stripe-Signature` header. Because this timestamp is part of the signed payload, it’s also verified by the signature, so an attacker can’t change the timestamp without invalidating the signature. If the signature is valid but the timestamp is too old, you can have your application reject the payload.

Our libraries have a default tolerance of 5 minutes between the timestamp and the current time. You can change this tolerance by providing an additional parameter when verifying signatures. Use Network Time Protocol ([NTP](https://en.wikipedia.org/wiki/Network_Time_Protocol)) to make sure that your server’s clock is accurate and synchronizes with the time on Stripe’s servers.

> Don’t use a tolerance value of `0`. Using a tolerance value of `0` disables the recency check entirely.

Stripe generates the timestamp and signature each time we send an event to your endpoint. If Stripe retries an event (for example, your endpoint previously replied with a non-`2xx` status code), then we generate a new signature and timestamp for the new delivery attempt.

### Quickly return a 2xx response 

Your [endpoint](https://docs.stripe.com/webhooks.md#example-endpoint) must quickly return a successful status code (`2xx`) prior to any complex logic that could cause a timeout. For example, you must return a `200` response before updating a customer’s invoice as paid in your accounting system.

## See also

- [Send events to Amazon EventBridge](https://docs.stripe.com/event-destinations/eventbridge.md)
- [List of thin event types](https://docs.stripe.com/api/v2/events/event-types.md)
- [List of snapshot event types](https://docs.stripe.com/api/events/.md)
- [Interactive webhook endpoint builder](https://docs.stripe.com/webhooks/quickstart.md)
