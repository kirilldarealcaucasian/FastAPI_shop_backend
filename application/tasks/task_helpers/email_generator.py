from email.message import EmailMessage

from application.tasks.email_config.email_config import email_settings


def create_order_confirmation_template(
        data: dict,
) -> EmailMessage:
    email = EmailMessage()

    email["Subject"] = "Order details"
    email["From"] = email_settings.SMTP_USER
    email["To"] = data["email"]
    # email["To"] = "pexy_slider@mail.ru"

    details = []
    total_price = 0

    for product_detail in data["products"]:
        details.append(
            f"""
            <ul>
            <li>product: {product_detail["name"]}</li>
            <li>count ordered: {product_detail["count_ordered"]}</li>
            <li>price per unit: {product_detail["total_price"]}$</li>
            </ul>
            """
        )
        total_price += product_detail["total_price"]

    email.set_content(
        f"""
        <h1>Hello, {data["username"]}!</h1>
        <p>Your order details:</p>
        """ + "/".join(details)
            + "- " * 10 + f"<p>Total:{total_price}$</p>"
                          ,subtype="html")
    return email