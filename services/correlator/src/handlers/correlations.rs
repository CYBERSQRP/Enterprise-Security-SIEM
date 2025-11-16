use actix_web::{web, HttpResponse, Responder, Scope};

pub fn configure() -> Scope {
    web::scope("/correlations")
        .route("", web::get().to(list_correlations))
        .route("/{id}", web::get().to(get_correlation))
}

async fn list_correlations() -> impl Responder {
    HttpResponse::Ok().json(serde_json::json!({
        "correlations": []
    }))
}

async fn get_correlation(path: web::Path<String>) -> impl Responder {
    HttpResponse::Ok().json(serde_json::json!({
        "id": path.into_inner()
    }))
}
