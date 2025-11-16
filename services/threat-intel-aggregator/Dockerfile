# Multi-stage build for Threat Intel Aggregator
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Install dependencies
RUN apk add --no-cache git ca-certificates

# Copy go mod files
COPY go.mod go.sum* ./
RUN go mod download || true

# Copy source code
COPY . .

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o threat-intel-aggregator .

# Final stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

# Copy binary from builder
COPY --from=builder /app/threat-intel-aggregator .

# Expose ports
EXPOSE 8080 9090

CMD ["./threat-intel-aggregator"]
