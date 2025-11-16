FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY shared/ ./shared/
COPY services/collector/ ./services/collector/

# Build the application
WORKDIR /app/services/collector
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o /collector main.go

# Final stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

COPY --from=builder /collector .

EXPOSE 514/udp

CMD ["./collector"]
