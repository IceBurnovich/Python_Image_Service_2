import logging
import math
import os
import uuid

import psycopg2
from flask import Flask, flash, redirect, render_template, request, send_from_directory, url_for

import crud

IMAGE_DIR = os.path.abspath(os.getenv("IMAGE_DIR", "images"))
LOG_DIR = os.path.abspath(os.getenv("LOG_DIR", "logs"))
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif"}
PER_PAGE = 10

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("docbox")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(os.path.join(LOG_DIR, "app.log"), encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(file_handler)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev")


@app.route("/")
def index():
    images_count = crud.get_images_count()
    return render_template("index.html", images_count=images_count)


@app.route("/upload", methods=["POST"])
def upload():
    image = request.files.get("file")
    if not image or image.filename == "":
        flash("Файл не выбран")
        return redirect(url_for("index"))

    extension = image.filename.rsplit(".", 1)[-1].lower() if "." in image.filename else ""
    if extension not in ALLOWED_EXTENSIONS:
        flash(f"Недопустимый формат: {extension or 'без расширения'}")
        return redirect(url_for("index"))

    filename = f"{uuid.uuid4().hex}.{extension}"
    file_path = os.path.join(IMAGE_DIR, filename)
    try:
        image.save(file_path)
        size = os.path.getsize(file_path)
        crud.save_image(filename, image.filename, size, extension)
    except (OSError, psycopg2.Error):
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                logger.exception("Не удалось удалить файл после ошибки загрузки: %s", file_path)
        logger.exception("Ошибка загрузки изображения: %s", image.filename)
        flash("Не удалось сохранить изображение")
        return redirect(url_for("index"))

    logger.info("Изображение загружено: %s", filename)
    flash(f"Файл сохранён как {filename}")
    return redirect(url_for("index"))


@app.route("/images-list")
def images_list():
    page = request.args.get("page", 1, type=int) or 1
    page = max(page, 1)
    query = request.args.get("q", "").strip()
    total = crud.get_images_count(query)
    total_pages = max(1, math.ceil(total / PER_PAGE))
    page = min(page, total_pages)
    images = crud.get_images(page, PER_PAGE, query)
    return render_template(
        "images_list.html",
        images=images,
        page=page,
        total_pages=total_pages,
        query=query,
    )


@app.route("/images/<path:name>")
def serve_image(name):
    return send_from_directory(IMAGE_DIR, name)


@app.route("/delete/<int:image_id>", methods=["POST"])
def delete_image(image_id):
    image = crud.get_image_by_id(image_id)
    if image is None:
        logger.warning("Изображение не найдено для удаления: %s", image_id)
        flash("Изображение не найдено")
        return redirect(url_for("images_list"))

    try:
        deleted = crud.delete_image(image_id)
    except psycopg2.Error:
        logger.exception("Ошибка удаления записи изображения: %s", image_id)
        flash("Не удалось удалить изображение")
        return redirect(url_for("images_list"))

    if deleted:
        file_path = os.path.join(IMAGE_DIR, image["filename"])
        try:
            os.remove(file_path)
        except FileNotFoundError:
            logger.warning("Файл изображения отсутствует: %s", file_path)
        except OSError:
            logger.exception("Ошибка удаления файла изображения: %s", file_path)
            flash("Запись удалена, но файл не удалось удалить")
            return redirect(url_for("images_list"))
        logger.info("Изображение удалено: %s", image["filename"])
        flash("Изображение удалено")

    return redirect(url_for("images_list"))


@app.route("/images-filter", methods=["POST"])
def images_filter():
    query = request.form.get("q", "").strip()
    return redirect(url_for("images_list", q=query) if query else url_for("images_list"))


@app.route("/documents-list")
def old_documents_list():
    return redirect(url_for("images_list"))


@app.route("/documents/<path:name>")
def old_serve_document(name):
    return redirect(url_for("serve_image", name=name))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
