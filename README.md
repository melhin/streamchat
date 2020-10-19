# StreamChat 

Is an attempt to make a completely self reliant redis stream chat using #fastapi.

This project is heavily influenced by the [redis-streams-fastapi-chat](https://github.com/leonh/redis-streams-fastapi-chat)

My attempts would be to

* Refactor the single file and add a structure to it
* Add a basic authentication mechanism
* Make the new message feature available for the chat

Since this looks like an app to experiment with. I have gone ahead and used it for testing isolated environments on kubernetes

Checkout [DevSpace](https://devspace.sh). Its an amazing tool to enable local development on kubernetes

#### Please Note: The main purpose of this repo is demonstration of how to structure fastapi and redis stream chat usecase
#### This is not a production ready application

## Docker Compose

You can use docker compose to make this work.
```
docker-compose up
```
Point your browser to [local](http://127.0.0.1:8000/)


## Dev Space

The ```devspace.yaml``` is provided in the root.
This defines the various componenets and their implementation

I have provided a sample_env in this repository. Change the values and rename it to .env

And then

```
devspace dev
```
