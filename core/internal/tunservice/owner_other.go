//go:build !windows && !linux

package tunservice

import (
	"errors"
	"net/netip"
)

// ownerPath finds no program here: no program skips the VPN, and
// no refused UDP names one.
func ownerPath(bool, netip.AddrPort) (string, error) {
	return "", errors.ErrUnsupported
}
