use actix_web::{web, HttpResponse, Responder, Scope};
use crate::engine::CorrelationEngine;
use std::sync::Arc;

pub fn configure() -> Scope {
    web::scope("/stats")
        .route("", web::get().to(get_stats))
}

async fn get_stats(engine: web::Data<Arc<CorrelationEngine>>) -> impl Responder {
    match engine.get_stats().await {
        Ok(stats) => HttpResponse::Ok().json(stats),
        Err(e) => HttpResponse::InternalServerError().json(serde_json::json!({
            "error": e.to_string()
        })),
    }
}
