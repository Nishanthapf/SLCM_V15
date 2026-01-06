#!/usr/bin/env python3
"""
Quick Setup Script - Run this directly
Usage: bench execute slcm.quick_setup.run
"""

import frappe


def run():
	"""One command setup - creates everything"""
	from slcm.setup_student_workflow import setup_student_master_workflow

	setup_student_master_workflow()
