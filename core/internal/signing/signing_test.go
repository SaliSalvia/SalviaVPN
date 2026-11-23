package signing

import (
	"crypto/ed25519"
	"encoding/base64"
	"errors"
	"strings"
	"testing"
)

// withKey sets Key to pub for the test.
func withKey(t *testing.T, pub ed25519.PublicKey) {
	t.Helper()
	old := Key
	Key = base64.StdEncoding.EncodeToString(pub)
	t.Cleanup(func() { Key = old })
}

func sign(priv ed25519.PrivateKey, data []byte) []byte {
	return []byte(base64.StdEncoding.EncodeToString(ed25519.Sign(priv, data)) + "\n")
}

func TestASignatureByTheKeyIsAccepted(t *testing.T) {
	pub, priv, _ := ed25519.GenerateKey(nil)
	withKey(t, pub)
	data := []byte("abc  Firefox-VPN-1.2.3-Windows-x64.zip\n")
	if err := Verify(data, sign(priv, data)); err != nil {
		t.Fatal(err)
	}
}

func TestAdditionalTrustedKeyIsAccepted(t *testing.T) {
	oldPrimary, oldAdditional := Key, AdditionalKeys
	t.Cleanup(func() {
		Key, AdditionalKeys = oldPrimary, oldAdditional
	})

	primaryPub, _, _ := ed25519.GenerateKey(nil)
	newPub, newPriv, _ := ed25519.GenerateKey(nil)
	Key = base64.StdEncoding.EncodeToString(primaryPub)
	AdditionalKeys = base64.StdEncoding.EncodeToString(newPub)

	data := []byte("release manifest")
	if err := Verify(data, sign(newPriv, data)); err != nil {
		t.Fatalf("signature by additional trusted key was rejected: %v", err)
	}
}

func TestMalformedAdditionalKeyFailsClosed(t *testing.T) {
	oldPrimary, oldAdditional := Key, AdditionalKeys
	t.Cleanup(func() {
		Key, AdditionalKeys = oldPrimary, oldAdditional
	})

	pub, priv, _ := ed25519.GenerateKey(nil)
	Key = base64.StdEncoding.EncodeToString(pub)
	AdditionalKeys = "not-a-valid-public-key"

	data := []byte("release manifest")
	if err := Verify(data, sign(priv, data)); err == nil || !strings.Contains(err.Error(), "additional update key is broken") {
		t.Fatalf("malformed additional key was not rejected: %v", err)
	}
}

func TestOtherSignaturesAreRefused(t *testing.T) {
	pub, priv, _ := ed25519.GenerateKey(nil)
	_, other, _ := ed25519.GenerateKey(nil)
	withKey(t, pub)
	data := []byte("data")
	for name, sig := range map[string][]byte{
		"another key": sign(other, data),
		"other data":  sign(priv, []byte("changed")),
		"unreadable":  []byte("not base64!"),
		"empty":       nil,
	} {
		if err := Verify(data, sig); err == nil {
			t.Errorf("%s: accepted", name)
		}
	}
}

func TestABuildWithoutAKeyChecksNothing(t *testing.T) {
	_, priv, _ := ed25519.GenerateKey(nil)
	old := AdditionalKeys
	AdditionalKeys = ""
	t.Cleanup(func() { AdditionalKeys = old })

	withKey(t, nil)
	Key = ""
	if Available() {
		t.Fatal("available without a key")
	}
	if err := Verify([]byte("x"), sign(priv, []byte("x"))); !errors.Is(err, ErrNoKey) {
		t.Fatalf("got %v", err)
	}
	Key = "broken"
	if err := Verify([]byte("x"), sign(priv, []byte("x"))); err == nil || !strings.Contains(err.Error(), "broken") {
		t.Fatalf("broken key: %v", err)
	}
}
