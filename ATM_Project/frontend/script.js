const $ = (id) => document.getElementById(id);
let selectedAction = "deposit";

async function api(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) }
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Something went wrong.");
  return data;
}

function showMessage(element, message, success = false) {
  element.textContent = message;
  element.className = success ? "message success" : "message";
}

function money(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency", currency: "INR", maximumFractionDigits: 2
  }).format(value);
}

function showDashboard(account) {
  $("loginView").classList.add("hidden");
  $("dashboardView").classList.remove("hidden");
  $("holderName").textContent = account.holder_name;
  $("accountType").textContent = account.account_type.toUpperCase() + " ACCOUNT";
  $("accountDisplay").textContent = account.account_number;
  $("balance").textContent = money(account.balance);
  loadTransactions();
}

async function refreshAccount() {
  const account = await api("/api/me");
  $("balance").textContent = money(account.balance);
  $("holderName").textContent = account.holder_name;
  $("accountType").textContent = account.account_type.toUpperCase() + " ACCOUNT";
}

$("loginForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  showMessage($("loginMessage"), "Signing in...");
  try {
    const account = await api("/api/login", {
      method: "POST",
      body: JSON.stringify({
        account_number: $("accountNumber").value.trim(),
        pin: $("pin").value.trim()
      })
    });
    $("pin").value = "";
    showDashboard(account);
  } catch (error) {
    showMessage($("loginMessage"), error.message);
  }
});

document.querySelectorAll(".action-tab").forEach((button) => {
  button.addEventListener("click", () => {
    selectedAction = button.dataset.action;
    document.querySelectorAll(".action-tab").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    const isPin = selectedAction === "changePin";
    $("moneyForm").classList.toggle("hidden", isPin);
    $("pinForm").classList.toggle("hidden", !isPin);
    $("amountLabel").textContent = selectedAction === "deposit" ? "Deposit amount (₹)" : "Withdrawal amount (₹)";
    $("moneyButton").textContent = selectedAction === "deposit" ? "Deposit money →" : "Withdraw money →";
    showMessage($("actionMessage"), "");
  });
});

$("moneyForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const amount = Number($("amount").value);
  try {
    const result = await api(`/api/${selectedAction}`, {
      method: "POST", body: JSON.stringify({ amount })
    });
    showMessage($("actionMessage"), result.message, true);
    $("amount").value = "";
    $("balance").textContent = money(result.balance);
    await loadTransactions();
  } catch (error) {
    showMessage($("actionMessage"), error.message);
  }
});

$("pinForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const result = await api("/api/change-pin", {
      method: "POST",
      body: JSON.stringify({
        old_pin: $("oldPin").value,
        new_pin: $("newPin").value
      })
    });
    showMessage($("actionMessage"), result.message, true);
    $("oldPin").value = "";
    $("newPin").value = "";
  } catch (error) {
    showMessage($("actionMessage"), error.message);
  }
});

async function loadTransactions() {
  try {
    const items = await api("/api/transactions");
    const container = $("transactions");
    if (!items.length) {
      container.innerHTML = '<p class="empty">No transactions yet.</p>';
      return;
    }
    container.innerHTML = items.map((item) => {
      const isCredit = item.transaction_type === "Deposit";
      const date = new Date(item.created_at.replace(" ", "T") + "Z");
      return `<div class="transaction">
        <div><div class="transaction-title">${item.transaction_type}</div>
        <div class="transaction-date">${date.toLocaleString()}</div></div>
        <div class="transaction-amount ${isCredit ? "credit" : "debit"}">
          ${isCredit ? "+" : "−"}${money(item.amount)}</div>
      </div>`;
    }).join("");
  } catch (error) {
    showMessage($("actionMessage"), error.message);
  }
}

$("refreshButton").addEventListener("click", async () => {
  await refreshAccount();
  await loadTransactions();
});

$("logoutButton").addEventListener("click", async () => {
  try {
    await api("/api/logout", { method: "POST" });
    $("dashboardView").classList.add("hidden");
    $("loginView").classList.remove("hidden");
    $("loginForm").reset();
    showMessage($("loginMessage"), "You have logged out.", true);
  } catch (error) {
    showMessage($("actionMessage"), error.message);
  }
});

// Restore the dashboard after a page refresh if the session is still active.
(async function restoreSession() {
  try {
    const account = await api("/api/me");
    showDashboard(account);
  } catch (_) {
    // Not logged in; keep the login screen visible.
  }
})();
