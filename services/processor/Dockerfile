FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY shared/ ./shared/
COPY services/processor/ ./services/processor/

# Build the application
WORKDIR /app/services/processor
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o /processor main.go

# Final stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

COPY --from=builder /processor .

CMD ["./processor"]
