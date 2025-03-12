from celery import Celery, Task
from kombu import serialization
import dill

def setup_celery(app):
    # Register dill serialization
    serialization.register(
        name='dill',
        encoder=dill.dumps,
        decoder=dill.loads,
        content_type='application/octet-stream'
    )

    # Create Celery instance
    celery = Celery(
        "app",
        broker="redis://localhost:6379/0",
        backend="redis://localhost:6379/0"
    )

    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = FlaskTask
    celery.config_from_object(app.config["CELERY"])
    app.extensions["celery"] = celery
    
    return celery 