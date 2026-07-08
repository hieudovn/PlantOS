"""WebServer — aiohttp server for Local Edge Console (port 8011).

Clean rewrite (NOT copied from Edge v1 web.py). Serves static files
from edge-v2/console/static/ and API routes from agent.web.routes.
No global module variables.
"""

import logging
from pathlib import Path

from aiohttp import web

from agent.auth.middleware import auth_middleware_factory
from agent.web.routes.auth import register_auth_routes
from agent.web.routes.status import register_status_routes
from agent.web.routes.config import register_config_routes
from agent.web.routes.connections import register_connection_routes
from agent.web.routes.processing import register_processing_routes
from agent.web.routes.backup import register_backup_routes
from agent.web.routes.support import register_support_routes

logger = logging.getLogger(__name__)


class WebServer:
    """Local Edge Console web server (port 8011).

    Constructor accepts all dependencies — no global state.
    Serves static files and JSON API routes. Auth middleware
    protects all /api/* routes except login/setup/status.
    """

    def __init__(self, config=None, auth=None, buffer=None,
                 connectors=None, processing=None, sync=None, health=None):
        self.config = config
        self.auth = auth
        self.buffer = buffer
        self.connectors = connectors
        self.processing = processing
        self.sync = sync
        self.health = health
        self._app: web.Application | None = None
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None

    def _build_app(self) -> web.Application:
        """Build the aiohttp application with all routes and middleware."""
        app = web.Application(middlewares=[
            # Auth middleware — protects /api/* routes
            auth_middleware_factory(self.auth),
        ])

        # ---- Static file serving -----------------------------------------
        # Serve HTML pages and static assets from console/static/
        static_dir = Path(__file__).resolve().parent.parent.parent / "console" / "static"
        if static_dir.exists():
            # Serve individual HTML files at root
            app.router.add_static("/", static_dir, show_index=False)
            logger.info("Serving static files from %s", static_dir)
        else:
            logger.warning("Static directory not found: %s", static_dir)

        # ---- API routes --------------------------------------------------
        register_auth_routes(app, self.auth)
        register_status_routes(app, self.buffer, self.sync, self.health,
                               self.config, self.connectors, self.processing,
                               auth=self.auth)
        register_config_routes(app, self.config)
        register_connection_routes(app, self.config, self.connectors)
        register_processing_routes(app, self.processing, self.config)
        register_backup_routes(app, self.config)
        register_support_routes(app, self.config, self.connectors, self.buffer, self.processing)

        return app

    async def start(self):
        """Start the web server."""
        self._app = self._build_app()
        port = self.config.web_port if self.config else 8011

        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, "0.0.0.0", port)
        await self._site.start()
        logger.info("Web server started on port %d", port)

    async def stop(self):
        """Stop the web server gracefully."""
        if self._runner:
            await self._runner.cleanup()
            logger.info("Web server stopped")

    async def handle_health(self) -> dict:
        """Placeholder for status route health check dependency."""
        return {}
