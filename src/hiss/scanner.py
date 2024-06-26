"""Contains the ClamAVScanner class, which handles the actual scanning and database update functionality"""

import asyncio
import inspect
from io import BytesIO

from hiss.logger import Hisss
from .update import FreshClam
from hiss.options import ScannerOptions as Options
from starlette.datastructures import UploadFile

hisss = Hisss()


class Scanner:
    """Scanner class for scanning files for malware.

    Attributes:
        - options (ClamAVScannerOptions): The options/flags to pass to the scanner (default: ClamAVScannerOptions())
    """

    def __init__(
        self,
        options: Options = Options(),
    ):
        self.options = options.build_command_list()

    async def scan_file(self, file: BytesIO):
        """Scans a BytesIO object for malware.

        Args:
            file (BytesIO | UploadFile): The BytesIO object containing the file to scan.

        Returns:
            bool: Returns True if file is clean, else False
        """

        if inspect.iscoroutinefunction(file.seek):
            return await self._scan_upload_file(file)

        else:
            return await self._scan_non_upload_file(file)

    async def _scan_upload_file(self, file: UploadFile):
        # Ensure the signature database is up-to-date before scanning
        await self.update_database()

        # Add the file path to the command
        full_command = self.options + ["-"]

        process = await asyncio.create_subprocess_exec(
            *full_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        await file.seek(0)
        stdout, stderr = await process.communicate(await file.read())
        if stdout:
            hisss.debug(msg=stdout.decode())
        if stderr:
            hisss.debug(msg=stderr.decode())

        if process.returncode == 0:
            hisss.info(msg="No virus detected.")
            return True
        elif process.returncode == 1:
            hisss.warning(msg="Virus detected.")
            return False
        else:
            hisss.error(msg="Error scanning.")
            return False

    async def _scan_non_upload_file(self, file: BytesIO):
        # Ensure the signature database is up-to-date before scanning
        await self.update_database()

        # Add the file path to the command
        full_command = self.options + ["-"]

        process = await asyncio.create_subprocess_exec(
            *full_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        file.seek(0)
        stdout, stderr = await process.communicate(file.getvalue())
        if stdout:
            hisss.debug(msg=stdout.decode())
        if stderr:
            hisss.debug(msg=stderr.decode())

        if process.returncode == 0:
            hisss.info(msg="No virus detected.")
            return True
        elif process.returncode == 1:
            hisss.warning(msg="Virus detected.")
            return False
        else:
            hisss.error(msg="Error scanning.")
            return False

    async def update_database(self):
        fresh_clam = FreshClam()
        await fresh_clam.update()
