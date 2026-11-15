import ctypes
import logging
import subprocess
import sys
import threading


class RainmeterErrorHandler(logging.Handler):
    def __init__(self, settings_file, executable):
        super().__init__(logging.ERROR)
        self.settings_file = settings_file
        self.executable = executable

    def emit(self, record):
        # Rainmeter writes this setting when the user toggles debug mode.
        if not ctypes.windll.kernel32.GetPrivateProfileIntW(
            "Rainmeter", "Debug", 0, self.settings_file
        ):
            return

        # The Rainmeter log viewer displays one line per entry. A double quote
        # would terminate the message argument in Rainmeter's bang parser.
        message = " | ".join(self.format(record).splitlines()).replace('"', "'")
        try:
            subprocess.run(
                [self.executable, "!Log", "EdifierMR5 Python - " + message[-16000:], "Error"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=True,
            )
        except (OSError, subprocess.SubprocessError):
            self.handleError(record)


def report_thread_error(args):
    if args.exc_type is not SystemExit:
        logging.error(
            "Thread %s", args.thread.name,
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )


if __name__ == "__main__":
    settings_file, executable = sys.argv[1:]
    logging.basicConfig(handlers=[RainmeterErrorHandler(settings_file, executable)], level=logging.ERROR)
    threading.excepthook = report_thread_error

    try:
        from mr5_service import main
        main(executable)
    except Exception:
        logging.exception("Service startup or main loop (%s)", sys.executable)
        sys.exit(1)
