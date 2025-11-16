use actix_web::{web, HttpResponse, Responder, Scope};
use crate::engine::CorrelationEngine;
use std::sync::Arc;

pub fn configure() -> Scope {
    web::scope("/rules")
        .route("", web::get().to(list_rules))
        .route("", web::post().to(create_rule))
        .route("/{id}", web::get().to(get_rule))
        .route("/{id}", web::put().to(update_rule))
        .route("/{id}", web::delete().to(delete_rule))
        .route("/reload", web::post().to(reload_rules))
}

async fn list_rules() -> impl Responder {
    HttpResponse::Ok().json(serde_json::json!({
        "rules": []
    }))
}

async fn create_rule() -> impl Responder {
    HttpResponse::Created().json(serde_json::json!({
        "status": "created"
    }))
}

async fn get_rule(path: web::Path<String>) -> impl Responder {
    HttpResponse::Ok().json(serde_json::json!({
        "id": path.into_inner()
    }))
}

async fn update_rule() -> impl Responder {
    HttpResponse::Ok().json(serde_json::json!({
        "status": "updated"
    }))
}

async fn delete_rule() -> impl Responder {
    HttpResponse::NoContent().finish()
}

async fn reload_rules(engine: web::Data<Arc<CorrelationEngine>>) -> impl Responder {
    match engine.reload_rules().await {
        Ok(_) => HttpResponse::Ok().json(serde_json::json!({
            "status": "reloaded"
        })),
        Err(e) => HttpResponse::InternalServerError().json(serde_json::json!({
            "error": e.to_string()
        })),
    }
}
