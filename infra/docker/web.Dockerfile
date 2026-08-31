# syntax=docker/dockerfile:1.7@sha256:a57df69d0ea827fb7266491f2813635de6f17269be881f696fbfdf2d83dda33e
# Pins the base image used for this reproducible container stage.
FROM node:24.18.0-bookworm-slim@sha256:6f7b03f7c2c8e2e784dcf9295400527b9b1270fd37b7e9a7285cf83b6951452d AS builder

# Sets the working directory for the container instructions that follow.
WORKDIR /build

# Runs the command required to prepare or start this container stage.
RUN npm install --global pnpm@10.28.2

# Copies only the required build input into the container image.
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
# Copies only the required build input into the container image.
COPY apps/web/package.json apps/web/package.json
# Copies only the required build input into the container image.
COPY packages/api_client/package.json packages/api_client/package.json
# Copies only the required build input into the container image.
COPY packages/shared_config/package.json packages/shared_config/package.json

# Runs the command required to prepare or start this container stage.
RUN pnpm install --frozen-lockfile

# Copies only the required build input into the container image.
COPY apps/web apps/web
# Copies only the required build input into the container image.
COPY packages/api_client packages/api_client
# Copies only the required build input into the container image.
COPY packages/shared_config packages/shared_config

# Performs this required step in the script or container workflow.
ARG NEXT_PUBLIC_API_ORIGIN
# Performs this required step in the script or container workflow.
ARG NEXT_PUBLIC_PRODUCT_ORIGIN
# Performs this required step in the script or container workflow.
ARG NEXT_PUBLIC_PRODUCT_NAME=Cipherboard
# Performs this required step in the script or container workflow.
ARG NEXT_PUBLIC_SUPPORT_EMAIL
# Performs this required step in the script or container workflow.
ARG NEXT_PUBLIC_LEGAL_ENTITY
# Performs this required step in the script or container workflow.
ARG NEXT_PUBLIC_JURISDICTION
# Performs this required step in the script or container workflow.
ARG NEXT_PUBLIC_POLICY_DATE

# Defines the environment used by subsequent container instructions.
ENV NEXT_PUBLIC_API_ORIGIN=${NEXT_PUBLIC_API_ORIGIN} \
    NEXT_PUBLIC_PRODUCT_ORIGIN=${NEXT_PUBLIC_PRODUCT_ORIGIN} \
    NEXT_PUBLIC_PRODUCT_NAME=${NEXT_PUBLIC_PRODUCT_NAME} \
    NEXT_PUBLIC_SUPPORT_EMAIL=${NEXT_PUBLIC_SUPPORT_EMAIL} \
    NEXT_PUBLIC_LEGAL_ENTITY=${NEXT_PUBLIC_LEGAL_ENTITY} \
    NEXT_PUBLIC_JURISDICTION=${NEXT_PUBLIC_JURISDICTION} \
    NEXT_PUBLIC_POLICY_DATE=${NEXT_PUBLIC_POLICY_DATE} \
    NEXT_TELEMETRY_DISABLED=1

# Runs the command required to prepare or start this container stage.
RUN pnpm --filter @mastermind/web build \
    && pnpm --filter @mastermind/web deploy --legacy --prod /runtime

# Pins the base image used for this reproducible container stage.
FROM node:24.18.0-bookworm-slim@sha256:6f7b03f7c2c8e2e784dcf9295400527b9b1270fd37b7e9a7285cf83b6951452d AS runtime

# Defines the environment used by subsequent container instructions.
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    VALIDATE_LAUNCH_CONFIGURATION=true \
    HOSTNAME=0.0.0.0 \
    PORT=3000

# Runs the command required to prepare or start this container stage.
RUN groupadd --system --gid 10001 mastermind \
    && useradd --system --uid 10001 --gid mastermind --home-dir /app mastermind \
    && rm -rf /usr/local/lib/node_modules/npm \
    && rm -f /usr/local/bin/npm /usr/local/bin/npx

# Sets the working directory for the container instructions that follow.
WORKDIR /app

# Copies only the required build input into the container image.
COPY --from=builder --chown=mastermind:mastermind /runtime ./
# Copies only the required build input into the container image.
COPY --from=builder --chown=mastermind:mastermind /build/apps/web/.next ./.next

# Drops privileges by selecting the runtime user for later instructions.
USER 10001:10001

# Documents the network port served by the container.
EXPOSE 3000

# Defines the probe used to determine whether the container is healthy.
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD ["node", "-e", "fetch('http://127.0.0.1:3000/').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"]

# Performs this required step in the script or container workflow.
STOPSIGNAL SIGTERM

# Runs the command required to prepare or start this container stage.
CMD ["node_modules/.bin/next", "start", ".", "-H", "0.0.0.0", "-p", "3000"]
