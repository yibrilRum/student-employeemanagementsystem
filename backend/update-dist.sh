#!/bin/bash

# Get the current config and ETag
aws cloudfront get-distribution --id E16YIM9QB4EC13 --query "Distribution.{Config:DistributionConfig, ETag:ETag}" --output json > dist.json

# Add DefaultRootObject
jq '.Config.DefaultRootObject = "index.html"' dist.json > tmp.json && mv tmp.json dist.json

# Add the EC2 origin (if not already present)
# First, check if origin already exists
if ! jq '.Config.Origins.Items[] | select(.Id == "ec2-origin")' dist.json > /dev/null 2>&1; then
    # Create new origin JSON
    cat > new-origin.json << 'ORIGIN'
{
  "Id": "ec2-origin",
  "DomainName": "204.236.210.174",
  "OriginPath": "",
  "CustomHeaders": {"Quantity": 0},
  "CustomOriginConfig": {
    "HTTPPort": 80,
    "HTTPSPort": 443,
    "OriginProtocolPolicy": "http-only",
    "OriginSslProtocols": {"Quantity": 0},
    "OriginReadTimeout": 30,
    "OriginKeepaliveTimeout": 5
  },
  "ConnectionAttempts": 3,
  "ConnectionTimeout": 10,
  "OriginShield": {"Enabled": false}
}
ORIGIN
    # Merge origins
    jq --slurpfile new <(jq '.' new-origin.json) '.Config.Origins.Items += $new' dist.json > tmp.json && mv tmp.json dist.json
    rm new-origin.json
fi

# Add two behaviors
# Behavior for /auth/*
BEHAVIOR_AUTH=$(cat <<BEHAVIOR
{
  "PathPattern": "/auth/*",
  "TargetOriginId": "ec2-origin",
  "ViewerProtocolPolicy": "redirect-to-https",
  "AllowedMethods": {
    "Quantity": 7,
    "Items": ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"],
    "CachedMethods": {"Quantity": 2, "Items": ["GET", "HEAD"]}
  },
  "SmoothStreaming": false,
  "Compress": false,
  "LambdaFunctionAssociations": {"Quantity": 0},
  "FunctionAssociations": {"Quantity": 0},
  "FieldLevelEncryptionId": "",
  "CachePolicyId": "4135ea2d-6df8-44a3-9df3-4b5a84be39ad",
  "OriginRequestPolicyId": "b689b0a8-53d0-40ab-baf2-68738e2966ac",
  "ResponseHeadersPolicyId": "67f7725c-6f97-4210-82d7-5512b31e9d03"
}
BEHAVIOR
)

BEHAVIOR_EMPL=$(cat <<BEHAVIOR
{
  "PathPattern": "/employees/*",
  "TargetOriginId": "ec2-origin",
  "ViewerProtocolPolicy": "redirect-to-https",
  "AllowedMethods": {
    "Quantity": 7,
    "Items": ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"],
    "CachedMethods": {"Quantity": 2, "Items": ["GET", "HEAD"]}
  },
  "SmoothStreaming": false,
  "Compress": false,
  "LambdaFunctionAssociations": {"Quantity": 0},
  "FunctionAssociations": {"Quantity": 0},
  "FieldLevelEncryptionId": "",
  "CachePolicyId": "4135ea2d-6df8-44a3-9df3-4b5a84be39ad",
  "OriginRequestPolicyId": "b689b0a8-53d0-40ab-baf2-68738e2966ac",
  "ResponseHeadersPolicyId": "67f7725c-6f97-4210-82d7-5512b31e9d03"
}
BEHAVIOR
)

# Remove existing behaviors that match these patterns (if any)
jq '.Config.CacheBehaviors.Items = (.Config.CacheBehaviors.Items // [] | map(select(.PathPattern != "/auth/*" and .PathPattern != "/employees/*")))' dist.json > tmp.json && mv tmp.json dist.json

# Add new behaviors
jq --argjson b1 "$BEHAVIOR_AUTH" --argjson b2 "$BEHAVIOR_EMPL" '.Config.CacheBehaviors.Items += [$b1, $b2]' dist.json > tmp.json && mv tmp.json dist.json

# Ensure CacheBehaviors.Quantity is correct
jq '.Config.CacheBehaviors.Quantity = (.Config.CacheBehaviors.Items | length)' dist.json > tmp.json && mv tmp.json dist.json

# Extract ETag
ETAG=$(jq -r '.ETag' dist.json)

# Update distribution
aws cloudfront update-distribution --id E16YIM9QB4EC13 --distribution-config file://<(jq '.Config' dist.json) --if-match "$ETAG"
