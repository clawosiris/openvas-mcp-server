# gvm-mcp — MCP server for GVM/OpenVAS over the rust-gvm-api REST gateway.
#
#   docker build -t gvm-mcp .
#   docker run -e GVM_GATEWAY_URL=http://gateway:8080 \
#              -e GVM_USERNAME=admin -e GVM_PASSWORD_FILE=/run/secrets/gvm \
#              -p 127.0.0.1:8000:8000 gvm-mcp

FROM rust:1-bookworm AS builder
WORKDIR /build

# Cache the dependency graph separately from the source.
COPY Cargo.toml Cargo.lock ./
RUN mkdir -p src && echo "fn main() {}" > src/main.rs && echo "" > src/lib.rs \
    && cargo build --release --locked && rm -rf src

COPY src ./src
RUN touch src/main.rs src/lib.rs && cargo build --release --locked

# Distroless: no shell, no package manager; rustls means no OpenSSL needed.
FROM gcr.io/distroless/cc-debian12:nonroot
COPY --from=builder /build/target/release/gvm-mcp /gvm-mcp

ENV MCP_TRANSPORT=streamable-http \
    MCP_BIND_ADDR=0.0.0.0:8000 \
    MCP_ALLOWED_HOSTS=*

EXPOSE 8000
USER nonroot
ENTRYPOINT ["/gvm-mcp"]
