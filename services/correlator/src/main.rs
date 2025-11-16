use actix_web::{web, App, HttpResponse, HttpServer, Responder};
use log::{info, error};
use std::sync::Arc;

mod config;
mod engine;
mod models;
mod rules;
mod storage;
mod handlers;

use engine::CorrelationEngine;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    env_logger::init();

    info!("Starting SIEM Correlation Engine v{}", env!("CARGO_PKG_VERSION"));

    // Load configuration
    let cfg = config::Config::from_env().expect("Failed to load configuration");

    // Initialize correlation engine
    let engine = Arc::new(
        CorrelationEngine::new(cfg.clone())
            .await
            .expect("Failed to initialize correlation engine")
    );

    // Start background correlation worker
    let engine_worker = engine.clone();
    tokio::spawn(async move {
        if let Err(e) = engine_worker.start().await {
            error!("Correlation engine error: {}", e);
        }
    });

    info!("Starting HTTP server on {}:{}", cfg.server.host, cfg.server.port);

    HttpServer::new(move || {
        App::new()
            .app_data(web::Data::new(engine.clone()))
            .route("/health", web::get().to(health_check))
            .service(
                web::scope("/api/v1")
                    .service(handlers::rules::configure())
                    .service(handlers::correlations::configure())
                    .service(handlers::stats::configure())
            )
    })
    .bind((cfg.server.host.as_str(), cfg.server.port))?
    .run()
    .await
}

async fn health_check() -> impl Responder {
    HttpResponse::Ok().json(serde_json::json!({
        "status": "healthy",
        "service": "correlation-engine",
        "version": env!("CARGO_PKG_VERSION")
    }))
}
