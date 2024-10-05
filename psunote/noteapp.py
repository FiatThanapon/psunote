import flask

import models
import forms


app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql://coe:CoEpasswd@localhost:5432/coedb"

models.init_app(app)


@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()
    return flask.render_template(
        "index.html",
        notes=notes,
    )


@app.route("/notes/create", methods=["GET", "POST"])
def notes_create():
    form = forms.NoteForm()
    if not form.validate_on_submit():
        print("error", form.errors)
        return flask.render_template(
            "notes-create.html",
            form=form,
        )
    note = models.Note()
    form.populate_obj(note)
    note.tags = []

    db = models.db
    for tag_name in form.tags.data:
        tag = (
            db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
            .scalars()
            .first()
            )

        if not tag:
            tag = models.Tag(name=tag_name)
            db.session.add(tag)

        note.tags.append(tag)

    db.session.add(note)
    db.session.commit()

    return flask.redirect(flask.url_for("index"))

@app.route("/tags/<tag_name>")
def tags_view(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()

    return flask.render_template(
        "tags-view.html",
        tag_name=tag_name,
        notes=notes,
    )

#######edit note#################
@app.route("/notes/<int:note_id>/edit", methods=["GET", "POST"])
def notes_edit(note_id):
    db = models.db

    # Fetch the note from the database
    note = db.session.execute(
        db.select(models.Note).where(models.Note.id == note_id)
    ).scalars().first()

    if not note:
        return "Note not found", 404

    # Initialize the form and set note object
    form = forms.NoteForm()

    if form.validate_on_submit():
        # Update note data if the form is valid
        note.title = form.title.data
        note.description = form.description.data
        note.tags = []  # Clear current tags

        for tag_name in form.tags.data:
            if isinstance(tag_name, str) and tag_name.strip():
                # Check if tag exists, otherwise create a new one
                tag = db.session.execute(
                    db.select(models.Tag).where(models.Tag.name == tag_name)
                ).scalars().first()

                if not tag:
                    tag = models.Tag(name=tag_name)
                    db.session.add(tag)

                note.tags.append(tag)  # Add the tag to the note

        db.session.commit()  # Commit changes to the database
        return flask.redirect(flask.url_for("index"))

    # Populate form with existing data on GET request
    if flask.request.method == "GET":
        form.title.data = note.title
        form.description.data = note.description
        form.tags.data = [tag.name for tag in note.tags]  # Populate tags with names

    # Render the edit template with the form and note
    return flask.render_template("notes-edit.html", form=form, note=note)
###################
#######delete note#################
@app.route("/notes/<int:note_id>/delete/", methods=["POST"])
def notes_delete(note_id):
    db = models.db

    note = db.session.execute(
        db.select(models.Note).where(models.Note.id == note_id)
    ).scalars().first()

    if not note:
        return "Note not found", 404

    db.session.delete(note)
    db.session.commit()

    return flask.redirect(flask.url_for("index"))
###################

if __name__ == "__main__":
    app.run(debug=True)
