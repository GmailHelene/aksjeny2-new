#!/bin/bash

set -eu

# setup user's .npmrc file. GITHUB_TOKEN and GITHUB_ORG are expected to be set in the container's environment and are not unexpanded here.
printf '//npm.pkg.github.com/:_authToken=${GITHUB_TOKEN}\n${GITHUB_ORG}:registry=https://npm.pkg.github.com\n' > ~/.npmrc

