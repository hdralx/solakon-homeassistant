# Solakon Solar for Home Assistant

A Home Assistant custom integration for German solar installations managed
through the [Solakon app](https://app.solakon.de).

## What it does

This integration connects Home Assistant to the Solakon cloud API and exposes
your inverter (and any attached batteries) as native sensor entities. It is
specifically aimed at the **Growatt Neo-800M** balcony / micro-inverter shipped
by Solakon, which has built-in WiFi but **no documented local API** — the only
practical way to read live data is through Solakon's cloud.

Once configured, your generation data shows up in Home Assistant just like any
other sensor and can be used in the **Energy Dashboard**, automations, and
Lovelace cards.

## Why this exists

The Neo-800M cannot be queried locally. The official Growatt cloud (ShinePhone
/ server.growatt.com) does not see devices that were provisioned through the
Solakon white-label app — those devices are pinned to `app.solakon.de` and
authenticate against a Supabase backend. This integration speaks that exact
protocol so users with a Solakon-provisioned inverter can finally pull their
data into Home Assistant.

## Requirements

- Home Assistant **2024.1** or newer
- A working Solakon account (the same one you use in the mobile app)
- Internet access from your Home Assistant instance to `*.app.solakon.de`

## Installation

### Option 1: HACS (recommended)

1. In HACS, open **Integrations**, then the three-dot menu and choose
   **Custom repositories**.
2. Add `https://github.com/hdralx/solakon-homeassistant` as an
   **Integration** repository.
3. Install **Solakon Solar** from the HACS list.
4. Restart Home Assistant.

### Option 2: Manual

1. Copy the `custom_components/solakon/` folder from this repository into your
   Home Assistant `config/custom_components/` directory.
   The final path should look like
   `<config>/custom_components/solakon/__init__.py`.
2. Restart Home Assistant.

## Setup

After restarting:

1. Go to **Settings** -> **Devices & services** -> **Add Integration**.
2. Search for **Solakon Solar** and select it.
3. Enter the **email address** associated with your Solakon account and
   submit. Solakon will email you a one-time code (OTP / magic-link code).
4. Open the email, copy the code, and paste it into the **Code** field in
   Home Assistant.
5. The integration will validate the code, store the resulting tokens, and
   create one device per inverter in your account, with all sensors attached.

There is no password to enter and nothing to configure on the inverter
itself — authentication is identical to the mobile app's login flow.

## Sensors

For each inverter in your Solakon account:

| Sensor                  | Unit | Device class | State class       |
|-------------------------|------|--------------|-------------------|
| Current Power           | W    | `power`      | `measurement`     |
| Today's Energy          | kWh  | `energy`     | `total_increasing`|
| Total Lifetime Energy   | kWh  | `energy`     | `total_increasing`|
| Status                  | -    | -            | -                 |

If your account contains batteries, the following are added per battery:

| Sensor          | Unit | Device class | State class       |
|-----------------|------|--------------|-------------------|
| Current Power   | W    | `power`      | `measurement`     |
| Today's Energy  | kWh  | `energy`     | `total_increasing`|

The energy sensors use `total_increasing` and are compatible with the Home
Assistant **Energy Dashboard** out of the box.

## Limitations

- **Cloud only.** The Neo-800M has no local API. If `app.solakon.de` is down,
  no data flows into Home Assistant. There is no offline fallback.
- **5-minute update interval.** The Solakon backend itself only refreshes
  inverter readings roughly every five minutes. Polling faster from Home
  Assistant would not produce fresher data and would only burn API quota.
- **No PV1 / PV2 split.** The Neo-800M has two MPPT strings, but Solakon's
  aggregated endpoint only exposes the combined `currentPower`. Per-string
  voltage, current, or power are not available.
- **Single Solakon account per HA instance recommended.** Multiple accounts
  are technically supported (each goes through its own config flow), but
  unique IDs are scoped to email addresses.
- **Tokens are single-use on refresh.** The integration handles this with an
  `asyncio.Lock` so concurrent refreshes cannot race, but if you copy a
  config entry between Home Assistant instances, only one of them will keep
  working — the other will invalidate the shared refresh token on its next
  refresh.

## Troubleshooting

**"Invalid or expired code" during setup**
The OTP code from Solakon is short-lived (a few minutes) and single-use.
Request a new one by re-entering your email if it expired or you mistyped it.

**Integration loads but sensors stay `unavailable`**
Open **Settings** -> **System** -> **Logs** and filter for `solakon`. The
most common causes are:
- The Solakon API returned a non-200 status (transient — usually resolves on
  the next 5-minute poll).
- The refresh token was rejected. This happens if the same account is used
  by another Home Assistant instance or by repeated failed setups. Remove
  the integration and re-add it to obtain a fresh token pair.

**No devices appear after setup**
The Solakon API returned an empty `groups` list for your account. Verify in
the Solakon mobile app that your inverter is actually attached to the
account you logged in with.

**Energy Dashboard shows odd jumps**
The lifetime counter resets are tracked by Home Assistant via the
`total_increasing` state class, so a midnight reset of "Today's Energy" is
expected and handled correctly. If you see large negative deltas on the
**Total Lifetime Energy** sensor, please open an issue with the affected
time range.

To enable verbose logging, add this to `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.solakon: debug
```

## Disclaimer

This integration is not affiliated with, endorsed by, or supported by Solakon
GmbH or Growatt. It uses the same public HTTPS endpoints as the official
Solakon mobile app. Use at your own risk.
