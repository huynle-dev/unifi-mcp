"""Tests for the client IP settings functionality.

This module tests the set_client_ip_settings method in ClientManager.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


def _mock_connection():
    """Create a mock ConnectionManager that serves /rest/networkconf."""
    conn = MagicMock()
    conn.site = "default"
    conn.networks = [
        {"_id": "net-lan", "name": "Default", "purpose": "corporate", "ip_subnet": "192.168.1.1/24"},
        {"_id": "net-iot", "name": "IoT", "purpose": "corporate", "ip_subnet": "198.51.100.1/24"},
        {"_id": "net-wan", "name": "WAN", "purpose": "wan"},
    ]

    async def _request(api_request, _c=conn):
        if api_request.method == "get" and api_request.path == "/rest/networkconf":
            return list(_c.networks)
        return {}

    conn.request = AsyncMock(side_effect=_request)
    conn.get_cached = MagicMock(return_value=None)
    conn._update_cache = MagicMock()
    conn._invalidate_cache = MagicMock()
    conn.controller = MagicMock()
    conn.controller.clients = MagicMock()
    conn.controller.clients.update = AsyncMock()
    conn.controller.clients.values = MagicMock(return_value=[])
    conn.controller.clients_all = MagicMock()
    conn.controller.clients_all.update = AsyncMock()
    conn.controller.clients_all.values = MagicMock(return_value=[])
    conn.ensure_connected = AsyncMock(return_value=True)

    # ConnectionManager.refresh_handler() is how the managers refresh a
    # handler collection now; delegate to the same ``update()`` these
    # tests already stub so their setup keeps its meaning.
    async def _refresh_handler(name, _c=conn):
        return await getattr(_c.controller, name).update()

    conn.refresh_handler = _refresh_handler
    return conn


class TestClientIPSettings:
    """Tests for client IP settings operations."""

    @pytest.fixture
    def mock_connection(self):
        """Create a mock ConnectionManager."""
        return _mock_connection()

    @pytest.fixture
    def client_manager(self, mock_connection):
        """Create a ClientManager with mocked connection."""
        from unifi_core.network.managers.client_manager import ClientManager

        return ClientManager(mock_connection)

    @pytest.fixture
    def mock_client(self):
        """Create a mock client object."""
        client = MagicMock()
        client.mac = "aa:bb:cc:dd:ee:ff"
        client.raw = {
            "_id": "client123",
            "mac": "aa:bb:cc:dd:ee:ff",
            "hostname": "test-device",
            "noted": True,
        }
        return client

    @pytest.mark.asyncio
    async def test_set_fixed_ip(self, client_manager, mock_connection, mock_client):
        """Test setting a fixed IP address."""
        # Mock get_client_details to return the client
        mock_connection.controller.clients_all.values.return_value = [mock_client]
        mock_connection.request.return_value = {}

        result = await client_manager.set_client_ip_settings(
            client_mac="aa:bb:cc:dd:ee:ff",
            use_fixedip=True,
            fixed_ip="192.168.1.100",
        )

        assert result is True
        # Verify the API call
        call_args = mock_connection.request.call_args
        api_request = call_args[0][0]
        assert api_request.data["use_fixedip"] is True
        assert api_request.data["fixed_ip"] == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_set_fixed_ip_only_ip(self, client_manager, mock_connection, mock_client):
        """Test setting fixed IP by only providing the IP address."""
        mock_connection.controller.clients_all.values.return_value = [mock_client]
        mock_connection.request.return_value = {}

        result = await client_manager.set_client_ip_settings(
            client_mac="aa:bb:cc:dd:ee:ff",
            fixed_ip="192.168.1.100",
        )

        assert result is True
        call_args = mock_connection.request.call_args
        api_request = call_args[0][0]
        # Should auto-enable use_fixedip
        assert api_request.data["use_fixedip"] is True
        assert api_request.data["fixed_ip"] == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_disable_fixed_ip(self, client_manager, mock_connection, mock_client):
        """Test disabling fixed IP."""
        mock_connection.controller.clients_all.values.return_value = [mock_client]
        mock_connection.request.return_value = {}

        result = await client_manager.set_client_ip_settings(
            client_mac="aa:bb:cc:dd:ee:ff",
            use_fixedip=False,
        )

        assert result is True
        call_args = mock_connection.request.call_args
        api_request = call_args[0][0]
        assert api_request.data["use_fixedip"] is False
        assert api_request.data["fixed_ip"] == ""

    @pytest.mark.asyncio
    async def test_set_local_dns_record(self, client_manager, mock_connection, mock_client):
        """Test setting a local DNS record."""
        mock_connection.controller.clients_all.values.return_value = [mock_client]
        mock_connection.request.return_value = {}

        result = await client_manager.set_client_ip_settings(
            client_mac="aa:bb:cc:dd:ee:ff",
            local_dns_record_enabled=True,
            local_dns_record="mydevice.local",
        )

        assert result is True
        call_args = mock_connection.request.call_args
        api_request = call_args[0][0]
        assert api_request.data["local_dns_record_enabled"] is True
        assert api_request.data["local_dns_record"] == "mydevice.local"

    @pytest.mark.asyncio
    async def test_set_local_dns_only_hostname(self, client_manager, mock_connection, mock_client):
        """Test setting DNS by only providing the hostname."""
        mock_connection.controller.clients_all.values.return_value = [mock_client]
        mock_connection.request.return_value = {}

        result = await client_manager.set_client_ip_settings(
            client_mac="aa:bb:cc:dd:ee:ff",
            local_dns_record="mydevice.local",
        )

        assert result is True
        call_args = mock_connection.request.call_args
        api_request = call_args[0][0]
        # Should auto-enable local_dns_record_enabled
        assert api_request.data["local_dns_record_enabled"] is True
        assert api_request.data["local_dns_record"] == "mydevice.local"

    @pytest.mark.asyncio
    async def test_disable_local_dns(self, client_manager, mock_connection, mock_client):
        """Test disabling local DNS record."""
        mock_connection.controller.clients_all.values.return_value = [mock_client]
        mock_connection.request.return_value = {}

        result = await client_manager.set_client_ip_settings(
            client_mac="aa:bb:cc:dd:ee:ff",
            local_dns_record_enabled=False,
        )

        assert result is True
        call_args = mock_connection.request.call_args
        api_request = call_args[0][0]
        assert api_request.data["local_dns_record_enabled"] is False
        assert api_request.data["local_dns_record"] == ""

    @pytest.mark.asyncio
    async def test_set_both_ip_and_dns(self, client_manager, mock_connection, mock_client):
        """Test setting both fixed IP and DNS record."""
        mock_connection.controller.clients_all.values.return_value = [mock_client]
        mock_connection.request.return_value = {}

        result = await client_manager.set_client_ip_settings(
            client_mac="aa:bb:cc:dd:ee:ff",
            use_fixedip=True,
            fixed_ip="192.168.1.100",
            local_dns_record_enabled=True,
            local_dns_record="mydevice.local",
        )

        assert result is True
        call_args = mock_connection.request.call_args
        api_request = call_args[0][0]
        assert api_request.data["use_fixedip"] is True
        assert api_request.data["fixed_ip"] == "192.168.1.100"
        assert api_request.data["local_dns_record_enabled"] is True
        assert api_request.data["local_dns_record"] == "mydevice.local"

    @pytest.mark.asyncio
    async def test_client_not_found(self, client_manager, mock_connection):
        """Test raises UniFiNotFoundError when client missing."""
        from unifi_core.exceptions import UniFiNotFoundError

        mock_connection.controller.clients_all.values.return_value = []

        with pytest.raises(UniFiNotFoundError):
            await client_manager.set_client_ip_settings(
                client_mac="xx:xx:xx:xx:xx:xx",
                fixed_ip="192.168.1.100",
            )

    @pytest.mark.asyncio
    async def test_no_settings_provided(self, client_manager, mock_connection, mock_client):
        """Test returns False when no settings provided."""
        mock_connection.controller.clients_all.values.return_value = [mock_client]

        result = await client_manager.set_client_ip_settings(
            client_mac="aa:bb:cc:dd:ee:ff",
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_marks_unnoted_client_as_noted(self, client_manager, mock_connection):
        """Test marks unnoted client as noted before setting IP."""
        unnoted_client = MagicMock()
        unnoted_client.mac = "aa:bb:cc:dd:ee:ff"
        unnoted_client.raw = {
            "_id": "client123",
            "mac": "aa:bb:cc:dd:ee:ff",
            "hostname": "test-device",
            "noted": False,  # Client is not noted
        }
        mock_connection.controller.clients_all.values.return_value = [unnoted_client]
        mock_connection.request.return_value = {}

        await client_manager.set_client_ip_settings(
            client_mac="aa:bb:cc:dd:ee:ff",
            fixed_ip="192.168.1.100",
        )

        # get_client_details first probes /stat/sta (active clients) before falling
        # back to /rest/user, so we see: GET /stat/sta, PUT note=True, PUT fixed_ip.
        # Assert the noted request is among them rather than position-indexing.
        write_requests = [
            call[0][0]
            for call in mock_connection.request.call_args_list
            if getattr(call[0][0], "data", None) is not None
        ]
        assert any(r.data.get("noted") is True for r in write_requests)
        assert any(r.data.get("use_fixedip") is True for r in write_requests)

    @pytest.mark.asyncio
    async def test_invalidates_cache(self, client_manager, mock_connection, mock_client):
        """Test invalidates cache after update."""
        mock_connection.controller.clients_all.values.return_value = [mock_client]
        mock_connection.request.return_value = {}

        await client_manager.set_client_ip_settings(
            client_mac="aa:bb:cc:dd:ee:ff",
            fixed_ip="192.168.1.100",
        )

        mock_connection._invalidate_cache.assert_called()

    @pytest.mark.asyncio
    async def test_handles_api_error(self, client_manager, mock_connection, mock_client):
        """Test returns False on API error."""
        mock_connection.controller.clients_all.values.return_value = [mock_client]
        mock_connection.request.side_effect = Exception("API error")

        with pytest.raises(Exception):
            await client_manager.set_client_ip_settings(
                client_mac="aa:bb:cc:dd:ee:ff",
                fixed_ip="192.168.1.100",
            )

    @pytest.mark.asyncio
    async def test_client_missing_id(self, client_manager, mock_connection):
        """Test returns False when client has no _id."""
        client_without_id = MagicMock()
        client_without_id.mac = "aa:bb:cc:dd:ee:ff"
        client_without_id.raw = {
            "mac": "aa:bb:cc:dd:ee:ff",
            # No _id field
        }
        mock_connection.controller.clients_all.values.return_value = [client_without_id]

        result = await client_manager.set_client_ip_settings(
            client_mac="aa:bb:cc:dd:ee:ff",
            fixed_ip="192.168.1.100",
        )
        assert result is False


def _put_payloads(mock_connection):
    """Return the data of every write request, in call order."""
    return [
        call[0][0].data
        for call in mock_connection.request.call_args_list
        if call[0][0].method == "put" and getattr(call[0][0], "data", None) is not None
    ]


class TestFixedIpNetworkId:
    """UniFi rejects a fixed IP without network_id (api.err.InvalidNetworkId)."""

    @pytest.fixture
    def client_manager(self, mock_connection):
        from unifi_core.network.managers.client_manager import ClientManager

        return ClientManager(mock_connection)

    @pytest.fixture
    def mock_connection(self):
        return _mock_connection()

    @pytest.fixture
    def mock_client(self, mock_connection):
        client = MagicMock()
        client.mac = "aa:bb:cc:dd:ee:ff"
        client.raw = {"_id": "client123", "mac": "aa:bb:cc:dd:ee:ff", "hostname": "test-device", "noted": True}
        mock_connection.controller.clients_all.values.return_value = [client]
        return client

    @pytest.mark.asyncio
    async def test_enable_infers_network_from_subnet(self, client_manager, mock_connection, mock_client):
        result = await client_manager.set_client_ip_settings(
            client_mac="aa:bb:cc:dd:ee:ff", use_fixedip=True, fixed_ip="198.51.100.30"
        )

        assert result is True
        payload = _put_payloads(mock_connection)[-1]
        assert payload == {"use_fixedip": True, "fixed_ip": "198.51.100.30", "network_id": "net-iot"}

    @pytest.mark.asyncio
    async def test_fixed_ip_alone_infers_network(self, client_manager, mock_connection, mock_client):
        await client_manager.set_client_ip_settings(client_mac="aa:bb:cc:dd:ee:ff", fixed_ip="192.168.1.100")

        assert _put_payloads(mock_connection)[-1]["network_id"] == "net-lan"

    @pytest.mark.asyncio
    async def test_explicit_network_id_is_sent(self, client_manager, mock_connection, mock_client):
        await client_manager.set_client_ip_settings(
            client_mac="aa:bb:cc:dd:ee:ff", use_fixedip=True, fixed_ip="198.51.100.30", network_id="net-iot"
        )

        assert _put_payloads(mock_connection)[-1]["network_id"] == "net-iot"

    @pytest.mark.asyncio
    async def test_corrects_reservation_stored_on_wrong_network(self, client_manager, mock_connection, mock_client):
        """A record whose network_id disagrees with its fixed_ip is re-pointed to the matching network."""
        mock_client.raw.update({"use_fixedip": True, "fixed_ip": "198.51.100.45", "network_id": "net-lan"})

        await client_manager.set_client_ip_settings(
            client_mac="aa:bb:cc:dd:ee:ff", use_fixedip=True, fixed_ip="198.51.100.45"
        )

        assert _put_payloads(mock_connection)[-1]["network_id"] == "net-iot"

    @pytest.mark.asyncio
    async def test_enable_without_ip_uses_existing_fixed_ip(self, client_manager, mock_connection, mock_client):
        mock_client.raw.update({"use_fixedip": False, "fixed_ip": "198.51.100.45"})

        await client_manager.set_client_ip_settings(client_mac="aa:bb:cc:dd:ee:ff", use_fixedip=True)

        assert _put_payloads(mock_connection)[-1] == {
            "use_fixedip": True,
            "fixed_ip": "198.51.100.45",
            "network_id": "net-iot",
        }

    @pytest.mark.asyncio
    async def test_enable_without_any_ip_raises(self, client_manager, mock_connection, mock_client):
        from unifi_core.network.managers.client_manager import FixedIpNetworkError

        with pytest.raises(FixedIpNetworkError, match="fixed_ip"):
            await client_manager.set_client_ip_settings(client_mac="aa:bb:cc:dd:ee:ff", use_fixedip=True)
        assert _put_payloads(mock_connection) == []

    @pytest.mark.asyncio
    async def test_no_matching_network_raises_without_writing(self, client_manager, mock_connection, mock_client):
        from unifi_core.network.managers.client_manager import FixedIpNetworkError

        with pytest.raises(FixedIpNetworkError, match="No configured network"):
            await client_manager.set_client_ip_settings(
                client_mac="aa:bb:cc:dd:ee:ff", use_fixedip=True, fixed_ip="203.0.113.10"
            )
        assert _put_payloads(mock_connection) == []

    @pytest.mark.asyncio
    async def test_unknown_network_id_raises(self, client_manager, mock_connection, mock_client):
        from unifi_core.network.managers.client_manager import FixedIpNetworkError

        with pytest.raises(FixedIpNetworkError, match="not found"):
            await client_manager.set_client_ip_settings(
                client_mac="aa:bb:cc:dd:ee:ff", fixed_ip="198.51.100.30", network_id="net-missing"
            )
        assert _put_payloads(mock_connection) == []

    @pytest.mark.asyncio
    async def test_network_id_subnet_mismatch_raises(self, client_manager, mock_connection, mock_client):
        from unifi_core.network.managers.client_manager import FixedIpNetworkError

        with pytest.raises(FixedIpNetworkError, match="not inside"):
            await client_manager.set_client_ip_settings(
                client_mac="aa:bb:cc:dd:ee:ff", fixed_ip="198.51.100.30", network_id="net-lan"
            )
        assert _put_payloads(mock_connection) == []

    @pytest.mark.asyncio
    async def test_invalid_ip_raises(self, client_manager, mock_connection, mock_client):
        from unifi_core.network.managers.client_manager import FixedIpNetworkError

        with pytest.raises(FixedIpNetworkError, match="valid IPv4"):
            await client_manager.set_client_ip_settings(client_mac="aa:bb:cc:dd:ee:ff", fixed_ip="not-an-ip")

    @pytest.mark.asyncio
    async def test_overlapping_networks_require_explicit_id(self, client_manager, mock_connection, mock_client):
        from unifi_core.network.managers.client_manager import FixedIpNetworkError

        mock_connection.networks.append({"_id": "net-dup", "name": "Dup", "ip_subnet": "198.51.100.129/25"})

        with pytest.raises(FixedIpNetworkError, match="network_id"):
            await client_manager.set_client_ip_settings(client_mac="aa:bb:cc:dd:ee:ff", fixed_ip="198.51.100.200")

        await client_manager.set_client_ip_settings(
            client_mac="aa:bb:cc:dd:ee:ff", fixed_ip="198.51.100.200", network_id="net-dup"
        )
        assert _put_payloads(mock_connection)[-1]["network_id"] == "net-dup"

    @pytest.mark.asyncio
    async def test_disable_does_not_resolve_network(self, client_manager, mock_connection, mock_client):
        await client_manager.set_client_ip_settings(client_mac="aa:bb:cc:dd:ee:ff", use_fixedip=False)

        assert _put_payloads(mock_connection)[-1] == {"use_fixedip": False, "fixed_ip": ""}
        assert not any(call[0][0].path == "/rest/networkconf" for call in mock_connection.request.call_args_list)

    @pytest.mark.asyncio
    async def test_resolve_fixed_ip_network_returns_summary(self, client_manager, mock_connection):
        network = await client_manager.resolve_fixed_ip_network("198.51.100.30")

        assert network == {"network_id": "net-iot", "network_name": "IoT", "ip_subnet": "198.51.100.1/24"}

    @pytest.mark.asyncio
    async def test_resolve_accepts_wrapped_response(self, client_manager, mock_connection):
        networks = list(mock_connection.networks)

        async def _request(api_request):
            return {"meta": {"rc": "ok"}, "data": networks}

        mock_connection.request.side_effect = _request

        network = await client_manager.resolve_fixed_ip_network("192.168.1.7")
        assert network["network_id"] == "net-lan"


IOT_NETWORK = {"network_id": "net-iot", "network_name": "IoT", "ip_subnet": "198.51.100.1/24"}


@pytest.mark.asyncio
async def test_tool_preview_shows_resolved_network():
    from types import SimpleNamespace
    from unittest.mock import patch

    with patch("unifi_network_mcp.tools.clients.client_manager") as manager:
        manager.get_client_details = AsyncMock(
            return_value=SimpleNamespace(
                raw={"name": "printer", "use_fixedip": False, "fixed_ip": None, "network_id": "net-lan"}
            )
        )
        manager.resolve_fixed_ip_network = AsyncMock(return_value=IOT_NETWORK)
        manager.set_client_ip_settings = AsyncMock()
        from unifi_network_mcp.tools.clients import set_client_ip_settings

        result = await set_client_ip_settings("aa:bb:cc:dd:ee:ff", use_fixedip=True, fixed_ip="198.51.100.30")

    assert result["success"] is True
    assert result["requires_confirmation"] is True
    proposed = result["preview"]["proposed"]
    assert proposed["network_id"] == "net-iot"
    assert proposed["network_name"] == "IoT"
    assert result["preview"]["current"]["network_id"] == "net-lan"
    manager.resolve_fixed_ip_network.assert_awaited_once_with("198.51.100.30", network_id=None)
    manager.set_client_ip_settings.assert_not_awaited()


@pytest.mark.asyncio
async def test_tool_preview_reports_unresolvable_network():
    from types import SimpleNamespace
    from unittest.mock import patch

    from unifi_core.network.managers.client_manager import FixedIpNetworkError

    with patch("unifi_network_mcp.tools.clients.client_manager") as manager:
        manager.get_client_details = AsyncMock(return_value=SimpleNamespace(raw={"name": "printer"}))
        manager.resolve_fixed_ip_network = AsyncMock(
            side_effect=FixedIpNetworkError("No configured network contains 203.0.113.10; pass network_id.")
        )
        from unifi_network_mcp.tools.clients import set_client_ip_settings

        result = await set_client_ip_settings("aa:bb:cc:dd:ee:ff", fixed_ip="203.0.113.10")

    assert result["success"] is False
    assert "No configured network contains 203.0.113.10" in result["error"]


@pytest.mark.asyncio
async def test_tool_confirm_passes_resolved_network_id():
    from types import SimpleNamespace
    from unittest.mock import patch

    with patch("unifi_network_mcp.tools.clients.client_manager") as manager:
        manager.get_client_details = AsyncMock(return_value=SimpleNamespace(raw={"name": "printer"}))
        manager.resolve_fixed_ip_network = AsyncMock(return_value=IOT_NETWORK)
        manager.set_client_ip_settings = AsyncMock(return_value=True)
        from unifi_network_mcp.tools.clients import set_client_ip_settings

        result = await set_client_ip_settings(
            "aa:bb:cc:dd:ee:ff", use_fixedip=True, fixed_ip="198.51.100.30", network_id="net-iot", confirm=True
        )

    assert result["success"] is True
    assert result["settings"]["network_id"] == "net-iot"
    assert result["settings"]["network_name"] == "IoT"
    manager.set_client_ip_settings.assert_awaited_once_with(
        client_mac="aa:bb:cc:dd:ee:ff",
        use_fixedip=True,
        fixed_ip="198.51.100.30",
        network_id="net-iot",
        local_dns_record_enabled=None,
        local_dns_record=None,
    )


@pytest.mark.asyncio
async def test_tool_disable_does_not_resolve_network():
    from types import SimpleNamespace
    from unittest.mock import patch

    with patch("unifi_network_mcp.tools.clients.client_manager") as manager:
        manager.get_client_details = AsyncMock(return_value=SimpleNamespace(raw={"name": "printer"}))
        manager.resolve_fixed_ip_network = AsyncMock()
        manager.set_client_ip_settings = AsyncMock(return_value=True)
        from unifi_network_mcp.tools.clients import set_client_ip_settings

        result = await set_client_ip_settings("aa:bb:cc:dd:ee:ff", use_fixedip=False, confirm=True)

    assert result["success"] is True
    manager.resolve_fixed_ip_network.assert_not_awaited()


@pytest.mark.asyncio
async def test_tool_rejects_network_id_when_disabling():
    from unifi_network_mcp.tools.clients import set_client_ip_settings

    result = await set_client_ip_settings("aa:bb:cc:dd:ee:ff", use_fixedip=False, network_id="net-iot")

    assert result["success"] is False
    assert "network_id" in result["error"]
