import os
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from forms import *
import sys
from models import db_setup, Venue, Artist, Show


app = Flask(__name__)
moment = Moment(app)
db = db_setup(app)


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


def show_form_errors(fieldName, errorMessages):
    return flash(
        'Some errors on ' +
        fieldName.replace('_', ' ') +
        ': ' +
        ' '.join([str(message) for message in errorMessages]),
        'warning'
    )


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    areas = db.session.query(Venue.city, Venue.state). \
        distinct(Venue.city, Venue.state).order_by('state').all()
    data = []
    for area in areas:
        venues = Venue.query.filter_by(state=area.state, city=area.city).all()
        venue_data = []
        for venue in venues:
            shows = Show.query.filter_by(venue_id=venue.id).all()
            venue_data.append({
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': len(shows)
            })
        data.append({
            'city': area.city,
            'state': area.state,
            'venues': venue_data
        })

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST', 'GET'])
def search_venues():
    search_term = request.form.get('search_term', '')
    venues = Venue.query.filter(Venue.name.ilike("%" + search_term + "%")).all()
    response = {
        "count": len(venues),
        "data": []
    }
    for venue in venues:
        response["data"].append({
            'id': venue.id,
            'name': venue.name,
        })
    return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    data_venue = Venue.query.filter(Venue.id == venue_id).first()
    if data_venue is None:
        abort(404)
    shows = db.session.query(Show).join(Venue, Venue.id == Show.venue_id). \
        filter(Venue.id == venue_id).all()
    past_shows, upcoming_shows = [], []
    for show in shows:
        temp_show = {
            'artist_id': show.artist_id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
        }
        if show.start_time <= datetime.now():
            past_shows.append(temp_show)
        else:
            upcoming_shows.append(temp_show)

    data_venue.upcoming_shows = upcoming_shows
    data_venue.upcoming_shows_count = len(upcoming_shows)
    data_venue.past_shows = past_shows
    data_venue.past_shows_count = len(past_shows)
    return render_template('pages/show_venue.html', venue=data_venue)


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    data = request.form
    name = data['name']
    city = data['city']
    state = data['state']
    address = data['address']
    phone = data['phone']
    genres = data.getlist('genres')
    facebook_link = data['facebook_link']
    image_link = data['image_link']
    try:
        db.session.add(
            Venue(
                city=city,
                state=state,
                name=name,
                address=address,
                phone=phone,
                facebook_link=facebook_link,
                genres=genres,
                seeking_talent=False,
                website="",
                image_link=image_link
            ))
    except:
        error = True
    finally:
        if not error:
            db.session.commit()
            flash('Venue ' + request.form['name'] +
                  ' was successfully listed!')
        else:
            flash('An error occurred. Venue ' +
                  name + ' could not be listed.')
            db.session.rollback()
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    error = False

    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
    except Exception as e:
        error = True
        db.session.rollback()
        print(sys.exc_info())
        return render_template('errors/500.html', error=str(e))
    finally:
        db.session.close()

    if error:
        abort(400)
        flash(
            'An error occurred. Venue could not be deleted.',
            'danger'
        )
    else:
        flash(
            'Venue was successfully deleted!',
            'success'
        )
    return render_template('pages/home.html')
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage


@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    data_artists = []
    artists = Artist.query.with_entities(Artist.id, Artist.name).order_by('id').all()

    for artist in artists:
        upcoming_shows = db.session.query(Show).\
            filter(Show.artist_id == artist.id).filter(
            Show.start_time > datetime.now()).all()

        data_artists.append({
            'id': artist.id,
            'name': artist.name,
            'num_upcoming_shows': len(upcoming_shows)
        })

    return render_template('pages/artists.html', artists=data_artists)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '')
    artists = Artist.query.filter(Artist.name.ilike("%" + search_term + "%")).all()
    response = {
        "count": len(artists),
        "data": []
    }
    for artist in artists:
        response["data"].append({
            'id': artist.id,
            'name': artist.name,
        })

    return render_template('pages/search_artists.html', results=response, search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    data_artist = Artist.query.filter(Artist.id == artist_id).first()
    if data_artist is None:
        abort(404)
    shows = db.session.query(Show).join(Artist, Artist.id == Show.artist_id). \
        filter(Artist.id == artist_id).all()
    past_shows, upcoming_shows = [], []
    for show in shows:
        temp_show = {
            'venue_id': show.venue_id,
            'venue_name': show.venue.name,
            'venue_image_link': show.venue.image_link,
            'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
        }
        if show.start_time <= datetime.now():
            past_shows.append(temp_show)
        else:
            upcoming_shows.append(temp_show)

    data_artist.upcoming_shows = upcoming_shows
    data_artist.upcoming_shows_count = len(upcoming_shows)
    data_artist.past_shows = past_shows
    data_artist.past_shows_count = len(past_shows)
    return render_template('pages/show_artist.html', artist=data_artist)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.filter(Artist.id == artist_id).first()

    form = ArtistForm()
    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.genres.data = artist.genres
    form.image_link.data = artist.image_link
    form.facebook_link.data = artist.facebook_link
    form.website_link.data = artist.website
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    error = False
    form = ArtistForm(request.form, meta={"csrf": False})

    name = form['name']
    city = form['city']
    state = form['state']
    phone = form['phone']
    genres = form.getlist('genres')
    image_link = form['image_link']
    facebook_link = form['facebook_link']
    website = form['website_link']
    seeking_talent = True if 'seeking_talent' in form else False
    seeking_description = form['seeking_description']

    try:
        artist = Artist.query.get(artist_id)
        artist.name = name
        artist.city = city
        artist.state = state
        artist.phone = phone
        artist.genres = genres
        artist.image_link = image_link
        artist.facebook_link = facebook_link
        artist.website = website
        artist.seeking_talent = seeking_talent
        artist.seeking_description = seeking_description

        db.session.commit()
    except Exception:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        abort(400)
        flash(
            'An error occurred. Artist '
            + name
            + ' could not be updated.',
            'danger'
        )
    else:
        flash(
            'Artist '
            + name
            + ' was successfully updated!',
            'success'
        )

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.filter(Venue.id == venue_id).first()

    form = VenueForm()
    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.address.data = venue.address
    form.phone.data = venue.phone
    form.genres.data = venue.genres
    form.image_link.data = venue.image_link
    form.facebook_link.data = venue.facebook_link
    form.website_link.data = venue.website
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    error = False

    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    image_link = request.form['image_link']
    facebook_link = request.form['facebook_link']
    website = request.form['website_link']
    seeking_talent = True if 'seeking_talent' in request.form else False
    seeking_description = request.form['seeking_description']

    try:
        venue = Venue.query.get(venue_id)

        venue.name = name
        venue.city = city
        venue.state = state
        venue.address = address
        venue.phone = phone
        venue.genres = genres
        venue.image_link = image_link
        venue.facebook_link = facebook_link
        venue.website = website
        venue.seeking_talent = seeking_talent
        venue.seeking_description = seeking_description
        db.session.commit()
    except Exception:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        abort(400)
        flash(
            'An error occurred. Venue '
            + name
            + ' could not be updated.',
            'danger'
        )
    else:
        flash(
            'Venue '
            + name
            + ' was successfully updated!',
            'success'
        )

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False
    form = ArtistForm()

    if not form.validate():
        for fieldName, errorMessages in form.errors.items():
            show_form_errors(fieldName, errorMessages)

        return redirect(url_for('create_artist_form'))

    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    image_link = request.form['image_link']
    facebook_link = request.form['facebook_link']
    website = request.form['website_link']
    seeking_venue = True if 'seeking_venue' in request.form else False
    seeking_description = request.form['seeking_description']

    try:
        artist = Artist(
            name=name,
            city=city,
            state=state,
            phone=phone,
            genres=genres,
            image_link=image_link,
            facebook_link=facebook_link,
            website=website,
            seeking_venue=seeking_venue,
            seeking_description=seeking_description,
        )

        db.session.add(artist)
        db.session.commit()
    except Exception:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        abort(400)
        flash(
            'An error occurred. Artist '
            + name
            + ' could not be listed.',
            'danger'
        )
    else:
        flash(
            'Artist '
            + name
            + ' was successfully listed!',
            'success'
        )

    return render_template('pages/home.html')

    # on successful db insert, flash success
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    data = []
    shows = db.session \
        .query(
        Venue.name,
        Artist.name,
        Artist.image_link,
        Show.venue_id,
        Show.artist_id,
        Show.start_time
    ) \
        .filter(Venue.id == Show.venue_id, Artist.id == Show.artist_id)

    for show in shows:
        data.append({
            'venue_name': show[0],
            'artist_name': show[1],
            'artist_image_link': show[2],
            'venue_id': show[3],
            'artist_id': show[4],
            'start_time': str(show[5])
        })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead

    error = False

    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']

    try:
        show = Show(
            artist_id=artist_id,
            venue_id=venue_id,
            start_time=start_time,
        )

        db.session.add(show)
        db.session.commit()
    except Exception:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        abort(400)
        flash(
            'An error occurred. Show could not be listed.',
            'danger'
        )
    else:
        flash(
            'Show was successfully listed!',
            'success'
        )

    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
# if __name__ == '__main__':
#     app.run()

# Or specify port manually:
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port)
