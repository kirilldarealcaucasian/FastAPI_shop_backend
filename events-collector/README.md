# events_collector

Minimal service that receives user-book interaction events and publishes them to Kafka.

If request payload contains `jwt_token`, service decodes it and, when claim `user_id` exists,
adds `user_id` to the produced Kafka message.
