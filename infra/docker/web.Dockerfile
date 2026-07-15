# syntax=docker/dockerfile:1.7@sha256:a57df69d0ea827fb7266491f2813635de6f17269be881f696fbfdf2d83dda33e
FROM node:24.18.0-bookworm-slim@sha256:6f7b03f7c2c8e2e784dcf9295400527b9b1270fd37b7e9a7285cf83b6951452d AS builder

WORKDIR /build

RUN npm install --global pnpm@10.28.2

COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/web/package.json apps/web/package.json
COPY packages/api_client/package.json packages/api_client/package.json
COPY packages/shared_config/package.json packages/shared_config/package.json

RUN pnpm install --frozen-lockfile

COPY apps/web apps/web
COPY packages/api_client packages/api_client
COPY packages/shared_config packages/shared_config

ARG NEXT_PUBLIC_API_ORIGIN
ARG NEXT_PUBLIC_PRODUCT_ORIGIN
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
ARG NEXT_PUBLIC_PRODUCT_NAME=Cipherboard
ARG NEXT_PUBLIC_SUPPORT_EMAIL
ARG NEXT_PUBLIC_LEGAL_ENTITY
ARG NEXT_PUBLIC_JURISDICTION
ARG NEXT_PUBLIC_POLICY_DATE

ENV NEXT_PUBLIC_API_ORIGIN=${NEXT_PUBLIC_API_ORIGIN} \
    NEXT_PUBLIC_PRODUCT_ORIGIN=${NEXT_PUBLIC_PRODUCT_ORIGIN} \
    NEXT_PUBLIC_SUPABASE_URL=${NEXT_PUBLIC_SUPABASE_URL} \
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=${NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY} \
    NEXT_PUBLIC_PRODUCT_NAME=${NEXT_PUBLIC_PRODUCT_NAME} \
    NEXT_PUBLIC_SUPPORT_EMAIL=${NEXT_PUBLIC_SUPPORT_EMAIL} \
    NEXT_PUBLIC_LEGAL_ENTITY=${NEXT_PUBLIC_LEGAL_ENTITY} \
    NEXT_PUBLIC_JURISDICTION=${NEXT_PUBLIC_JURISDICTION} \
    NEXT_PUBLIC_POLICY_DATE=${NEXT_PUBLIC_POLICY_DATE} \
    NEXT_TELEMETRY_DISABLED=1

RUN pnpm --filter @mastermind/web build \
    && pnpm --filter @mastermind/web deploy --legacy --prod /runtime

FROM node:24.18.0-bookworm-slim@sha256:6f7b03f7c2c8e2e784dcf9295400527b9b1270fd37b7e9a7285cf83b6951452d AS runtime

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    VALIDATE_LAUNCH_CONFIGURATION=true \
    HOSTNAME=0.0.0.0 \
    PORT=3000

RUN groupadd --system --gid 10001 mastermind \
    && useradd --system --uid 10001 --gid mastermind --home-dir /app mastermind \
    && rm -rf /usr/local/lib/node_modules/npm \
    && rm -f /usr/local/bin/npm /usr/local/bin/npx

WORKDIR /app

COPY --from=builder --chown=mastermind:mastermind /runtime ./
COPY --from=builder --chown=mastermind:mastermind /build/apps/web/.next ./.next

USER 10001:10001

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD ["node", "-e", "fetch('http://127.0.0.1:3000/').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"]

STOPSIGNAL SIGTERM

CMD ["node_modules/.bin/next", "start", ".", "-H", "0.0.0.0", "-p", "3000"]
