# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Flask (Python) with MySQL, served through a small Jinja/HTML front end and a lightweight JavaScript layer for browser interactions.

## Users

Primary users are barangay residents who need to register, log in, submit concerns, and monitor their status. Barangay administrators and staff manage the same concern workflow from an internal dashboard view.

## Product Purpose

BarangayAssist is a local barangay service portal for recording resident concerns and tracking issue status. It helps residents report problems or requests and gives barangay staff a shared dashboard to review, categorize, and resolve them.

## Positioning

This product occupies a practical civic operations workflow: it is not a broad community platform or a general CRM, but a focused local service and complaint-tracking system for barangay operations.

## Operating Context

The application is intended for local deployment in a barangay environment, with a MySQL database and server-side session handling. It relies on a default local admin account for setup and a resident/admin role model to separate public and staff workflows. The project is currently a Python app with templates under `templates/` and static assets under `static/`.

## Capabilities and Constraints

Confirmed capabilities include:

- Resident registration and login
- Resident dashboard showing concern records and counts
- Concern submission with title, description, category, and status
- Admin dashboard with aggregate counts for users and concerns
- Staff/admin visibility of concern records and status updates
- Local lockout logic for repeated failed login attempts
- MySQL-backed persistence with schema initialization in `schema.sql` and `app.py`

Confirmed constraints and product facts:

- No external identity provider or SSO is configured.
- Role-based access is enforced in code for resident and admin views.
- The default local admin credentials are seeded in code during DB initialization.
- The software is a web app rather than a mobile-native app.
- The current configuration is designed for local or small-team deployment and does not define a production cloud stack.

## Brand Commitments

The project name is "BarangayAssist". No formal brand system, logo package, or public-facing tone guide was found in the repository, so no additional binding brand rules are recorded here.

## Evidence on Hand

- `README.md` for project description and app behavior
- `app.py` for route structure, auth flows, admin/resident dashboards, and database initialization
- `schema.sql` for persistent data model
- `templates/` for the resident, admin, and concern-submission screens
- `static/` for styles and front-end assets

## Product Principles

1. Keep barangay service requests simple, visible, and trackable.
2. Separate resident-facing and staff-facing workflows through explicit roles.
3. Favor local, practical deployment over enterprise complexity.
4. Preserve transparent status tracking so residents know the current state of a concern.
5. Maintain a clear operational loop from report to resolution.

## Accessibility & Inclusion

No product-specific accessibility requirements were established in the repository. The application should continue to meet standard web accessibility expectations for forms, keyboard navigation, and readable contrast as future design work proceeds.
