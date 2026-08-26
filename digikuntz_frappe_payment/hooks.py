app_name = "digikuntz_frappe_payment"
app_title = "Digikuntz Frappe Payment"
app_publisher = "Digikuntz"
app_description = "Apps for all payment digikuntz"
app_email = "choudja@gic.cm"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "digikuntz_frappe_payment",
# 		"logo": "/assets/digikuntz_frappe_payment/logo.png",
# 		"title": "Digikuntz Frappe Payment",
# 		"route": "/digikuntz_frappe_payment",
# 		"has_permission": "digikuntz_frappe_payment.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/digikuntz_frappe_payment/css/digikuntz_frappe_payment.css"
app_include_js = [
    "/assets/frappe_digikuntz_flutterwave/js/payment_request.js",
    "/assets/frappe_digikuntz_flutterwave/js/sales_invoice.js"
]

# include js, css files in header of web template
# web_include_css = "/assets/digikuntz_frappe_payment/css/digikuntz_frappe_payment.css"
# web_include_js = "/assets/digikuntz_frappe_payment/js/digikuntz_frappe_payment.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "digikuntz_frappe_payment/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Company": "public/js/company.js"
    }
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "digikuntz_frappe_payment/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "digikuntz_frappe_payment.utils.jinja_methods",
# 	"filters": "digikuntz_frappe_payment.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "digikuntz_frappe_payment.install.before_install"
# after_install = "digikuntz_frappe_payment.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "digikuntz_frappe_payment.uninstall.before_uninstall"
after_uninstall = "digikuntz_frappe_payment.setup.install.after_install"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "digikuntz_frappe_payment.utils.before_app_install"
# after_app_install = "digikuntz_frappe_payment.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "digikuntz_frappe_payment.utils.before_app_uninstall"
# after_app_uninstall = "digikuntz_frappe_payment.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "digikuntz_frappe_payment.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"digikuntz_frappe_payment.tasks.all"
# 	],
# 	"daily": [
# 		"digikuntz_frappe_payment.tasks.daily"
# 	],
# 	"hourly": [
# 		"digikuntz_frappe_payment.tasks.hourly"
# 	],
# 	"weekly": [
# 		"digikuntz_frappe_payment.tasks.weekly"
# 	],
# 	"monthly": [
# 		"digikuntz_frappe_payment.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "digikuntz_frappe_payment.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "digikuntz_frappe_payment.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "digikuntz_frappe_payment.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "digikuntz_frappe_payment.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["digikuntz_frappe_payment.utils.before_request"]
# after_request = ["digikuntz_frappe_payment.utils.after_request"]

# Job Events
# ----------
# before_job = ["digikuntz_frappe_payment.utils.before_job"]
# after_job = ["digikuntz_frappe_payment.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"digikuntz_frappe_payment.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

