// Package signing checks the Ed25519 signatures of updates: the releases'
// SHA256SUMS.txt, which the Windows app checks before it installs a new
// version of itself (internal/update), and the TUN service's executable,
// which the installed service checks before it replaces itself
// (internal/tunservice). tools/sign makes the key and the signatures.
package signing

import (
	"crypto/ed25519"
	"encoding/base64"
	"errors"
	"strings"
)

// Key is the primary base64 Ed25519 public key set by the build from the
// private key used to sign the release. A build without Key takes no updates.
var Key string

// AdditionalKeys contains comma-separated base64 Ed25519 public keys that
// this build also trusts. It is used only during a deliberate key rotation:
// the transition build is still signed by the old private key (Key), while
// it learns to verify releases and TUN-service updates signed by the new key.
// After the transition release has reached installed clients, the primary
// key can be switched and the old key temporarily retained here.
//
// Public keys are not secrets. Never put a private key in source control.
var AdditionalKeys = "5HoqK9wcgt/UN7zGa/u/ccuI5DE9M3flXN3zIZWjcFs="

// ErrNoKey means this build has no primary update key, so it takes no updates.
var ErrNoKey = errors.New("this build has no update key, so it takes no updates")

// Available reports whether this build has a primary key and can check signatures.
func Available() bool { return Key != "" }

// trustedKeys decodes the primary key and all configured additional keys.
// A malformed configured key fails closed rather than being silently ignored.
func trustedKeys() ([]ed25519.PublicKey, error) {
	if Key == "" {
		return nil, ErrNoKey
	}
	encoded := []string{Key}
	for _, candidate := range strings.Split(AdditionalKeys, ",") {
		if candidate = strings.TrimSpace(candidate); candidate != "" {
			encoded = append(encoded, candidate)
		}
	}

	keys := make([]ed25519.PublicKey, 0, len(encoded))
	for i, value := range encoded {
		raw, err := base64.StdEncoding.DecodeString(value)
		if err != nil || len(raw) != ed25519.PublicKeySize {
			if i == 0 {
				return nil, errors.New("the build's update key is broken")
			}
			return nil, errors.New("an additional update key is broken")
		}
		keys = append(keys, ed25519.PublicKey(raw))
	}
	return keys, nil
}

// Verify checks sig, a base64 signature as tools/sign writes it (one line),
// over data against the primary key or any explicitly trusted additional key.
func Verify(data, sig []byte) error {
	keys, err := trustedKeys()
	if err != nil {
		return err
	}
	raw, err := base64.StdEncoding.DecodeString(strings.TrimSpace(string(sig)))
	if err != nil || len(raw) != ed25519.SignatureSize {
		return errors.New("the signature is unreadable")
	}
	for _, key := range keys {
		if ed25519.Verify(key, data, raw) {
			return nil
		}
	}
	return errors.New("the signature does not match")
}
