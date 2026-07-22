#!/bin/bash

gcloud config set project sdd-agy-cli-d69221667e
export GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project)
echo $GOOGLE_CLOUD_PROJECT