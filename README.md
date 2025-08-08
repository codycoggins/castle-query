# LLM Search Experiment




# Setup

## Start Qdrant in Docker
Qdrant is our local vector DB. Easiest way to run it:

```bash
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  qdrant/qdrant
```

Verify it’s up:

```bash
curl http://localhost:6333/collections
```

You should get {"collections": []}.


## Create Google Cloud project & enable Gmail API

We need OAuth credentials for Gmail access.

Go to: https://console.cloud.google.com/

Create a new project (e.g., gmail-search-llm)

Enable Gmail API

Go to APIs & Services → Credentials

Click Create credentials → OAuth client ID

Application type: Desktop App

Name: Local Dev Gmail

Download the JSON — rename it to credentials.json in your project folder.
