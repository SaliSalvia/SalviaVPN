//go:build !windows

package tunservice

// AdapterName is the TUN device's name (Linux allows no spaces; others name
// it utunN itself, tunstack).
const AdapterName = "salvia-vpn"
