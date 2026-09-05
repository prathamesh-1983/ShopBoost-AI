const API = "http://127.0.0.1:8000";


async function askAgent() {

    const message =
        document.getElementById("userMessage").value;

    if (!message.trim()) {
        alert("Please enter what you want to buy.");
        return;
    }

    document.getElementById("loading").innerText =
        "🤖 AI agent is thinking...";

    document.getElementById("result").innerHTML = "";

    try {

        const response = await fetch(
            `${API}/api/agent`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    message: message
                })
            }
        );

        const data = await response.json();

        document.getElementById("loading").innerText = "";

        if (!data.success) {

            document.getElementById("result").innerHTML =
                `<div class="card">
                    ❌ ${data.message}
                 </div>`;

            return;
        }

        showRecommendation(data);

    } catch (error) {

        document.getElementById("loading").innerText = "";

        document.getElementById("result").innerHTML =
            `<div class="card">
                ❌ Could not connect to AI agent.
             </div>`;
    }
}


function showRecommendation(data) {

    const product = data.product;
    const upsell = data.upsell;

    let html = `
        <div class="card">

            <h2>🤖 AI Recommendation</h2>

            <div class="product">

                <h2>${product.name}</h2>

                <p>${product.description}</p>

                <div class="price">
                    ₹${product.price}
                </div>

                <p class="reason">
                    <strong>Why AI selected it:</strong><br>
                    ${data.reason}
                </p>

                <button
                    class="buy-button"
                    onclick="buyProduct(
                        '${product.name}',
                        ${product.price}
                    )">
                    Proceed to Payment
                </button>

            </div>
    `;

    if (upsell) {

        html += `
            <div class="upsell">

                <h3>💡 AI Upsell Suggestion</h3>

                <strong>
                    ${upsell.name}
                </strong>

                <p>
                    ₹${upsell.price}
                </p>

                <p>
                    ${data.upsell_reason}
                </p>

                <button
                    onclick="buyProduct(
                        '${upsell.name}',
                        ${upsell.price}
                    )">
                    Buy Add-on
                </button>

            </div>
        `;
    }

    html += `</div>`;

    document.getElementById("result").innerHTML = html;
}


async function buyProduct(productName, price) {

    /*
       IMPORTANT:
       The customer has explicitly clicked
       the payment button.

       The AI itself cannot initiate payment.
    */

    try {

        const response = await fetch(
            `${API}/api/create-order`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    amount: price,
                    product_name: productName
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {

            alert(data.detail || "Order creation failed.");

            return;
        }

        const options = {

            key: data.key,

            amount: data.order.amount,

            currency: data.order.currency,

            name: "ShopBoost AI",

            description: productName,

            order_id: data.order.id,

            handler: async function(response) {

                await verifyPayment(response);
            },

            theme: {
                color: "#387ed1"
            }
        };

        const razorpay =
            new Razorpay(options);

        razorpay.open();

    } catch (error) {

        alert("Payment system error.");
    }
}


async function verifyPayment(response) {

    const result = await fetch(
        `${API}/api/verify-payment`,
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                razorpay_order_id:
                    response.razorpay_order_id,

                razorpay_payment_id:
                    response.razorpay_payment_id,

                razorpay_signature:
                    response.razorpay_signature
            })
        }
    );

    const data = await result.json();

    if (data.success) {

        document.getElementById("result").innerHTML += `
            <div class="card">

                <h2>✅ Payment Verified</h2>

                <p>
                    Your test payment was successfully verified.
                </p>

                <p>
                    Payment ID:
                    ${response.razorpay_payment_id}
                </p>

            </div>
        `;

    } else {

        alert(
            "Payment verification failed."
        );
    }
}