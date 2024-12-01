//go:build embed
// +build embed

package main

import (
	// "compress/zstd"
	"compress/gzip"

	"github.com/andybalholm/brotli"
	"github.com/klauspost/compress/zstd"

	"embed"
	"flag"
	"fmt"
	"io/fs"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
)

//go:embed static
var embed_static_fs embed.FS

// specify external static folder
var flg_external_static = flag.String("static", "", "Path to external static files, example ./static")

// extract builtin static for user custmize
var flg_extract = flag.String("extract", "", "Path to extract builtin static, example ./static_out")

func serve_builtin_static(prefix string) {
	fmt.Println("== serve from builtin static")
	fsys, _ := fs.Sub(embed_static_fs, "static")
	http.Handle(prefix+"/", http.StripPrefix(prefix, http.FileServer(http.FS(fsys))))
}

func extract_static(dest_dir string) error {
	// mkdir
	if _, err := os.Stat(dest_dir); os.IsNotExist(err) {
		err := os.MkdirAll(dest_dir, 0755)
		if err != nil {
			log.Fatalf("Failed to create extract directory: %v", err)
		}
		log.Println("++ Extract directory Created")
	} else {
		fmt.Println("== Extract directory Exists")
	}

	// extract
	err := fs.WalkDir(embed_static_fs, "static", func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}

		relPath := strings.TrimPrefix(path, "static")
		destPath := filepath.Join(dest_dir, relPath)

		if d.IsDir() {
			return os.MkdirAll(destPath, 0755)
		}

		data, err := embed_static_fs.ReadFile(path)
		if err != nil {
			return err
		}

		return os.WriteFile(destPath, data, 0644)
	})

	if err != nil {
		log.Fatalf("Failed to extract static files: %v", err)
	} else {
		fmt.Println("== builtin Static files extracted to", dest_dir)
	}

	return nil
}

func server_static(prefix string) {
	if *flg_extract != "" {
		extract_static(*flg_extract)
		return
	}

	if *flg_external_static == "" {
		// use builtin static
		fmt.Println("== serve from builtin static")
		fsys, _ := fs.Sub(embed_static_fs, "static")
		http.Handle(prefix+"/", http.StripPrefix(prefix, http.FileServer(http.FS(fsys))))
	} else {
		fmt.Println("-- serve from external static:", *flg_external_static)
		// use external static
		// http.Handle(prefix+"/", http.StripPrefix(prefix, http.FileServer(http.Dir(*flg_external_static))))
		http.Handle(prefix+"/", http.StripPrefix(prefix, compressionMiddleware(http.FileServer(http.Dir(*flg_external_static)))))

	}
}

// compressionMiddleware adds support for `Content-Encoding: zstd`, `gzip`, and `br` (Brotli).
func compressionMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		acceptEncoding := r.Header.Get("Accept-Encoding")

		if strings.Contains(acceptEncoding, "br") {
			// Handle Brotli encoding
			encoder := brotli.NewWriter(w)
			defer encoder.Close()

			w.Header().Set("Content-Encoding", "br")
			w.Header().Del("Content-Length") // Content length cannot be known with compression
			next.ServeHTTP(&compressedResponseWriter{ResponseWriter: w, writer: encoder}, r)
			return
		} else if strings.Contains(acceptEncoding, "zstd") {
			// Handle zstd encoding
			encoder, err := zstd.NewWriter(w)
			if err != nil {
				http.Error(w, "failed to create zstd writer", http.StatusInternalServerError)
				return
			}
			defer encoder.Close()

			w.Header().Set("Content-Encoding", "zstd")
			w.Header().Del("Content-Length") // Content length cannot be known with compression
			next.ServeHTTP(&compressedResponseWriter{ResponseWriter: w, writer: encoder}, r)
			return
		} else if strings.Contains(acceptEncoding, "gzip") {
			// Handle gzip encoding
			encoder := gzip.NewWriter(w)
			defer encoder.Close()

			w.Header().Set("Content-Encoding", "gzip")
			w.Header().Del("Content-Length") // Content length cannot be known with compression
			next.ServeHTTP(&compressedResponseWriter{ResponseWriter: w, writer: encoder}, r)
			return
		}

		// Fallback to normal handler if no supported encoding is found
		next.ServeHTTP(w, r)
	})
}

// compressedResponseWriter wraps the standard ResponseWriter to support compression.
type compressedResponseWriter struct {
	http.ResponseWriter
	writer interface {
		Write([]byte) (int, error)
	}
}

func (crw *compressedResponseWriter) Write(b []byte) (int, error) {
	return crw.writer.Write(b)
}
