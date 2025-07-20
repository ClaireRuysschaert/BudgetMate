from rest_framework import generics
from rest_framework.response import Response


class UploadFileView(generics.CreateAPIView):
    def post(self, request, *args, **kwargs):
        # Show content of csv file
        print(request.data["file"].read().decode("utf-8"))
        return Response({"message": "POST: Received a file!"})


def prompt_for_category(label: str, category_name: str, sub_category_name: str) -> tuple[str | None, str | None]:
    print(f"\nNew label detected: {label}")
    # Category input loop
    while True:
        cat_input = input(
            f"Proposed category: '{category_name}'. Type 'yes' to accept, or enter a new category (or 'q' to quit): "
        ).strip()
        if cat_input.lower() == "q":
            print("Input cancelled.")
            return None, None
        if cat_input.lower() in ["yes", "", "y"]:
            category = category_name
        else:
            category = cat_input if cat_input else category_name
        if category:
            break
        print("Please enter a category or quit.")

    # Sub-category input loop
    while True:
        subcat_input = input(
            f"Proposed sub-category: '{sub_category_name}'. Type 'yes' to accept, or enter a new sub-category (or 'q' to quit): "
        ).strip()
        if subcat_input.lower() == "q":
            print("Input cancelled.")
            return None, None
        if subcat_input.lower() in ["yes", "", "y"]:
            sub_category = sub_category_name
        else:
            sub_category = subcat_input if subcat_input else sub_category_name
        if sub_category:
            break
        print("Please enter a sub-category or quit.")

    return category.strip(), sub_category.strip()
