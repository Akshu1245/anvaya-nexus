from flask import Blueprint, current_app, g, request

from backend.anvaya.api.errors import ApiError
from backend.anvaya.schemas.common import SuccessEnvelope
from backend.anvaya.services.data_readiness import commit_import, get_import_job, validate_import
from backend.anvaya.services.generator import generate
from backend.anvaya.services.source_registry import list_sources

data_readiness_blueprint=Blueprint("data_readiness",__name__,url_prefix="/api")


def _ok(data,warnings=None,status=200):
    return SuccessEnvelope[dict|list](request_id=g.request_id,data=data,warnings=warnings or []).model_dump(mode="json"),status


@data_readiness_blueprint.get("/sources")
def sources(): return _ok(list_sources(current_app.extensions["repository"]))


@data_readiness_blueprint.post("/imports/validate")
def validate():
    upload=request.files.get("file")
    if not upload: raise ApiError("IMPORT_FILE_REQUIRED","Select a synthetic CSV or JSON file.",400,False)
    extension=upload.filename.rsplit(".",1)[-1].lower() if upload.filename and "." in upload.filename else ""
    return _ok(validate_import(current_app.extensions["repository"],upload.read(),extension,request.form.get("source_version","synthetic-import-1.0")),status=201)


@data_readiness_blueprint.post("/imports/<job_id>/commit")
def commit(job_id): return _ok(commit_import(current_app.extensions["repository"],job_id))


@data_readiness_blueprint.get("/imports/<job_id>")
def inspect(job_id): return _ok(get_import_job(current_app.extensions["repository"],job_id))


@data_readiness_blueprint.post("/development/seed")
def seed():
    if current_app.config["ENV_NAME"] not in {"development","testing"}: raise ApiError("DEVELOPMENT_ONLY","Seed loading is disabled.",404,False)
    payload=request.get_json(silent=True) or {}; return _ok(generate(current_app.extensions["repository"],current_app.config,payload.get("scale","test"),int(payload.get("seed",20260711))))
