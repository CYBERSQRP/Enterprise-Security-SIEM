FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY shared/ ./shared/
COPY services/api-gateway/ ./services/api-gateway/

# Build the application
WORKDIR /app/services/api-gateway
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o /api-gateway main.go

# Final stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

COPY --from=builder /api-gateway .

EXPOSE 8080

CMD ["./api-gateway"]
