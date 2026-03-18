from django.core.management.base import BaseCommand

from submission.models import Article
from core.models import File, Account
from plugins.pandoc_plugin import logic
from production import logic as production_logic
from utils.testing.helpers import Request


class Command(BaseCommand):
    help = "Generate PDFs with cover sheets for selected files of specified articles."

    def add_arguments(self, parser):
        parser.add_argument(
            "article_ids",
            nargs="+",
            type=int,
            help=(
                "IDs of the articles to process. "
                "Multiple IDs can be provided."
            ),
        )
        parser.add_argument(
            "--owner",
            type=str,
            required=True,
            help="Email or username of the account owner for the file.",
        )
        parser.add_argument(
            "--conversion_type",
            type=str,
            required=True,
            help="Either stamped or unstamped",
        )

    def handle(self, *args, **options):
        article_ids = options["article_ids"]
        conversion_type = options.get("conversion_type", "stamped")
        owner_identifier = options["owner"]

        try:
            owner = Account.objects.get(
                email=owner_identifier,
            )
        except Account.DoesNotExist:
            try:
                owner = Account.objects.get(username=owner_identifier)
            except Account.DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(
                        f"Account with email or username '{owner_identifier}' does not exist."
                    )
                )
                return

        for article_id in article_ids:
            try:
                article = Article.objects.get(pk=article_id)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Processing Article ID: {article_id} - {article.title}"
                    )
                )

                files = File.objects.filter(
                    article_id=article.pk,
                    is_galley=False,
                )
                if not files.exists():
                    self.stdout.write(
                        self.style.WARNING(
                            f"No files found for Article ID: {article_id}"
                        )
                    )
                    continue

                self.stdout.write("Available files:")
                file_choices = {
                    str(i): file
                    for i, file in enumerate(files, start=1)
                }
                for index, file in file_choices.items():
                    self.stdout.write(
                        f"{index}: {file.label} (MIME: {file.mime_type})"
                    )

                selected_indices = input(
                    "Enter the numbers of the files to process, "
                    "separated by commas (or press Enter to skip): "
                )
                if not selected_indices.strip():
                    self.stdout.write(
                        self.style.WARNING(
                            f"Skipping Article ID: {article_id}."
                        )
                    )
                    continue

                selected_files = [
                    file_choices[index.strip()]
                    for index in selected_indices.split(",")
                    if index.strip() in file_choices
                ]

                if not selected_files:
                    self.stdout.write(
                        self.style.WARNING(
                            f"No valid selections made for Article ID: {article_id}."
                        )
                    )
                    continue

                for file in selected_files:
                    try:
                        final_pdf_path, article = logic.generate_pdf_with_cover_sheet(
                            article_id=article.pk,
                            file_id=file.pk,
                            conversion_type=conversion_type,
                        )
                        request = Request()
                        request.user = owner
                        production_logic.save_galley(
                            article=article,
                            request=request,
                            uploaded_file=final_pdf_path,
                            is_galley=True,
                            label="PDF",
                            save_to_disk=False,
                            public=True,
                        )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Generated PDF for Article ID: {article.pk}, "
                                f"File ID: {file.pk}. "
                                f"Saved at {final_pdf_path}."
                            )
                        )
                    except Exception as e:
                        self.stderr.write(
                            self.style.ERROR(
                                f"Error processing File ID: {file.pk}. "
                                f"Error: {str(e)}"
                            )
                        )

            except Article.DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(
                        f"Article with ID {article_id} does not exist."
                    )
                )
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(
                        f"Error processing Article ID: {article_id}. "
                        f"Error: {str(e)}"
                    )
                )
