from setuptools import setup, find_packages
from pathlib import Path

VERSION = '1.0.2'
DESCRIPTION = 'zlapi: Zalo API for Python'
this_directory = Path(__file__).parent
LONG_DESCRIPTION = (this_directory / "README.md").read_text()

# Setting up
setup(
    name="zlapi",
    version=VERSION,
    author="devtt",
    author_email="<vrxxdev@gmail.com>",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=['requests', 'aiohttp', 'aenum', 'attr', 'pycryptodome', 'datetime', 'munch', 'websockets'],
    keywords=['python', 'zalo', 'api', 'zalo api', 'zalo chat', 'requests'],
    classifiers=[
		"Development Status :: 3 - Alpha",
		"Intended Audience :: Developers",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
		"Natural Language :: English",
		"Programming Language :: Python",
		"Programming Language :: Python :: 3",
		"Programming Language :: Python :: Implementation :: CPython",
		"Programming Language :: Python :: Implementation :: PyPy",
		"Topic :: Communications :: Chat",
		"Topic :: Internet :: WWW/HTTP",
		"Topic :: Internet :: WWW/HTTP :: Dynamic Content",
		"Topic :: Software Development :: Libraries",
		"Topic :: Software Development :: Libraries :: Python Modules"
    ]
)
# // 5755d9a3-aa67-4b1b-860f-031106a0f1b0-16453d6e2683b8800ded2a27c7f595d9
# // {"__zi":"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8yydkMgdKfNXtMSvQdMIbI3TPhafpCr.1","__zi-legacy":"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8yydkMgdKfNXtMSvQdMIbI3TPhafpCr.1","ozi":"2000.QOBlzDCV2uGerkFzm09IrMJTu_h42rNHBDtd_uyBLjKis-RnCpK.1","_hjSessionUser_3705269":"eyJpZCI6ImNmMmY0OGYzLWFiYjEtNWM4NC1hOTY4LTllMDEwYmM0MTNhOSIsImNyZWF0ZWQiOjE3MjkzOTAyMDc4MDIsImV4aXN0aW5nIjp0cnVlfQ==","_ga_C51H66N22P":"GS1.2.1729390207.1.1.1729390225.42.0.0","_ga_4QSSY47VGF":"GS1.2.1729390207.1.1.1729390225.42.0.0","_ga_GP4XVYJ45L":"GS1.1.1729390207.1.1.1729390225.42.0.0","_ga_NVN38N77J3":"GS1.2.1729389828.1.1.1729390279.0.0.0","_ga_E63JS7SPBL":"GS1.1.1729389430.1.1.1729390432.60.0.0","_ga_907M127EPP":"GS1.1.1733376909.4.0.1733376909.60.0.0","_ga":"GA1.2.429546685.1727146780","_ga_RYD7END4JE":"GS1.2.1741954876.19.1.1741955066.60.0.0","zpsid":"Jlpq.327895371.21.fEUevQPC-mRj1N0Lgapx1jC_YJMKUyC_at_CDum_KnjwfBevfvqCui5C-mO","zpw_sek":"hHrR.327895371.a0.QMPlDIGiUNflPV9f1InvUbyE71465bie4aLELMvOD3HIOmqVI5iiEnqPDbLJ4KHOMIrDpG3maJiRBQYDm4jvUW","app.event.zalo.me":"8640547388816798560","_zlang":"vn"}